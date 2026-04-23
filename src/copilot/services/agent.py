#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""LangGraph agent orchestrator — 6-node state machine for governance chat.

Per .idea/Plan/Architecture/Overview.md and AgentPipeline.md:

    classify_intent → select_tools → validate_proposal
                                         ↓
                              ┌─── is_write? ───┐
                              │ yes             │ no
                              ▼                 ▼
                         hitl_gate         execute_tool
                              │                 │
                              ▼                 ▼
                    (return pending)     format_response

Module G defense Layer 4: ALLOWED_TOOLS is the tool allowlist that the LLM
is constrained to. Anything outside raises ToolNotAllowlisted (HTTP 422).

State machine is per-request (stateless between HTTP calls per architecture).
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from copilot.clients import om_mcp, openai_client
from copilot.middleware.error_envelope import (
    LlmInvalidOutput,
    LlmUnavailable,
    McpAuthFailed,
    McpUnavailable,
    ToolNotAllowlisted,
)
from copilot.models import RiskLevel, ToolCallProposal, ToolCallRecord, ToolName
from copilot.models.chat import risk_level_for
from copilot.models.governance_state import GovernanceState
from copilot.observability import get_logger
from copilot.services import governance_store
from copilot.services.sessions import set_pending
from copilot.services.tool_audit import redact_tool_arguments, summarize_tool_result

log = get_logger(__name__)

# Module G Layer 4: server-side allowlist enforcement (defense-in-depth even
# though the Pydantic Literal type already constrains this).
ALLOWED_TOOLS: frozenset[ToolName] = frozenset(ToolName)

# HITL confirmation expiry per APIContract.md
CONFIRMATION_TTL = timedelta(minutes=5)

# Intent → system prompt hint mapping
INTENT_DESCRIPTIONS: dict[str, str] = {
    "search": "The user wants to search or browse metadata entities.",
    "classify": "The user wants to auto-classify columns with PII or governance tags.",
    "lineage": "The user wants to explore data lineage or impact analysis.",
    "rca": "The user wants root cause analysis on data quality issues.",
    "glossary": "The user wants to create or manage glossary terms.",
    "metric": "The user wants to create or view metrics.",
    "test": "The user wants to create or view data quality tests.",
    "multi_mcp": "The user wants a cross-platform workflow (e.g., OM + GitHub).",
}

# Valid intents
VALID_INTENTS = frozenset(INTENT_DESCRIPTIONS.keys())


# =============================================================================
# Agent State
# =============================================================================


class AgentState(TypedDict, total=False):
    """LangGraph state dict for a single chat turn.

    Fields mirror ChatSession but are stored as plain dict keys for
    LangGraph compatibility.
    """

    request_id: str
    session_id: str
    user_message: str
    intent: str | None
    tool_proposals: list[Any]
    tool_results: list[Any]
    tool_records: list[Any]
    pending_confirmation: dict[str, Any] | None
    final_response: str | None
    tokens_prompt: int
    tokens_completion: int
    error: str | None


def _initial_state(
    user_message: str,
    session_id: str | None = None,
    request_id: UUID | str | None = None,
) -> AgentState:
    """Create the initial state for a new chat turn."""
    rid = (
        request_id if isinstance(request_id, UUID) else UUID(request_id) if request_id else uuid4()
    )
    sid = UUID(session_id) if session_id else uuid4()
    return AgentState(
        request_id=str(rid),
        session_id=str(sid),
        user_message=user_message,
        intent=None,
        tool_proposals=[],
        tool_results=[],
        tool_records=[],
        pending_confirmation=None,
        final_response=None,
        tokens_prompt=0,
        tokens_completion=0,
        error=None,
    )


# =============================================================================
# Node 1: Classify Intent
# =============================================================================

_CLASSIFY_SYSTEM_PROMPT = """You are an intent classifier for an OpenMetadata governance agent.

Given the user's message, classify their intent into exactly ONE of these categories:
- search: searching or browsing metadata
- classify: auto-classifying columns with tags (PII, sensitivity)
- lineage: exploring data lineage or impact analysis
- rca: root cause analysis on data quality
- glossary: creating or managing glossary terms
- metric: creating or viewing metrics
- test: creating or managing data quality tests
- multi_mcp: cross-platform workflow involving external systems

Respond with ONLY a JSON object: {"intent": "<category>"}
"""


async def classify_intent(state: AgentState) -> AgentState:
    """Node 1: Use LLM to classify the user's intent.

    Args:
        state: Current agent state with ``user_message`` set.

    Returns:
        Updated state with ``intent`` set, or ``error`` on failure.
    """
    log.info("agent.classify_intent.start", request_id=state["request_id"])

    try:
        result = await openai_client.call_chat_json(
            messages=[
                {"role": "system", "content": _CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": state["user_message"]},
            ],
            max_tokens=50,
        )
        intent = result.get("intent", "search")
        if intent not in VALID_INTENTS:
            log.warning("agent.classify_intent.unknown", intent=intent)
            intent = "search"  # safe fallback

        state["intent"] = intent
        log.info("agent.classify_intent.complete", intent=intent)

    except (LlmUnavailable, LlmInvalidOutput) as exc:
        log.warning("agent.classify_intent.failed", error=str(exc))
        state["intent"] = "search"  # degrade gracefully
        state["error"] = f"Intent classification failed: {exc}"

    return state


# =============================================================================
# Node 2: Select Tools
# =============================================================================

_SELECT_TOOLS_SYSTEM_PROMPT = """You are a tool selector for an OpenMetadata governance agent.

Available tools (ONLY use these):
- search_metadata: Search tables, topics, dashboards by keyword
- semantic_search: Semantic/vector search across metadata
- get_entity_details: Get full details of a specific entity by FQN
- get_entity_lineage: Get upstream/downstream lineage for an entity
- create_glossary: Create a new glossary
- create_glossary_term: Create a term in a glossary
- create_lineage: Create a lineage edge between entities
- patch_entity: Modify an entity (add tags, change owner, update description)
- get_test_definitions: List available data quality test types
- create_test_case: Create a data quality test
- create_metric: Create a metric definition
- root_cause_analysis: Analyze root cause of data quality failures

Given the user's message and classified intent, select the tools to call and their arguments.

Respond with ONLY a JSON object:
{
  "tools": [
    {"name": "<tool_name>", "arguments": {<key>: <value>}}
  ],
  "rationale": "Brief explanation of why these tools were chosen"
}
"""

_DEMO_SERVICE_FILTER = "service:customer_db"
_DEMO_TABLE_FQN = "sample_mysql.default.customer_db.customers"
_DEMO_PII_COLUMNS: tuple[str, str, str] = ("email", "phone", "ssn")


def _auto_classification_proposals() -> list[dict[str, Any]]:
    """Return deterministic classify chain for demo-critical P2-01 flow."""
    return [
        {
            "name": "search_metadata",
            "arguments": {
                "query": "*",
                "entityType": "table",
                "queryFilter": _DEMO_SERVICE_FILTER,
            },
            "rationale": "Scan customer_db tables before classification.",
        },
        {
            "name": "get_entity_details",
            "arguments": {
                "entityType": "table",
                "entityFqn": _DEMO_TABLE_FQN,
            },
            "rationale": "Inspect target table columns before proposing tags.",
        },
        {
            "name": "patch_entity",
            "arguments": {
                "entityType": "table",
                "entityFqn": _DEMO_TABLE_FQN,
                "approved_tags": [f"{_DEMO_TABLE_FQN}.{column}:PII.Sensitive" for column in _DEMO_PII_COLUMNS],
                # Batch patch proposal for the three PII spot-check columns in seed/customer_db.json.
                "patch": [
                    {"op": "add", "path": "/columns/3/tags/-", "value": {"tagFQN": "PII.Sensitive"}},
                    {"op": "add", "path": "/columns/4/tags/-", "value": {"tagFQN": "PII.Sensitive"}},
                    {"op": "add", "path": "/columns/5/tags/-", "value": {"tagFQN": "PII.Sensitive"}},
                ],
            },
            "rationale": "Propose batch PII tagging for email/phone/ssn via HITL gate.",
        },
    ]


async def select_tools(state: AgentState) -> AgentState:
    """Node 2: Use LLM to select which MCP tools to call with what arguments.

    Args:
        state: Current state with ``intent`` and ``user_message``.

    Returns:
        Updated state with ``tool_proposals`` list populated.
    """
    log.info("agent.select_tools.start", request_id=state["request_id"], intent=state["intent"])

    if state.get("intent") == "classify":
        proposals = _auto_classification_proposals()
        state["tool_proposals"] = proposals
        log.info(
            "agent.select_tools.classify_chain",
            tool_count=len(proposals),
            tools=[p["name"] for p in proposals],
        )
        return state

    intent_hint = INTENT_DESCRIPTIONS.get(state["intent"] or "search", "")

    try:
        result = await openai_client.call_chat_json(
            messages=[
                {"role": "system", "content": _SELECT_TOOLS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Intent: {state['intent']}\n"
                        f"Hint: {intent_hint}\n"
                        f"User message: {state['user_message']}"
                    ),
                },
            ],
            max_tokens=500,
        )

        tools = result.get("tools", [])
        rationale = result.get("rationale", "")

        proposals = []
        for tool_spec in tools:
            tool_name = tool_spec.get("name", "")
            arguments = tool_spec.get("arguments", {})
            proposals.append(
                {
                    "name": tool_name,
                    "arguments": arguments,
                    "rationale": rationale,
                }
            )

        state["tool_proposals"] = proposals
        log.info(
            "agent.select_tools.complete",
            tool_count=len(proposals),
            tools=[p["name"] for p in proposals],
        )

    except (LlmUnavailable, LlmInvalidOutput) as exc:
        log.warning("agent.select_tools.failed", error=str(exc))
        state["error"] = f"Tool selection failed: {exc}"
        state["tool_proposals"] = []

    return state


# =============================================================================
# Node 3: Validate Proposal
# =============================================================================


def assert_tool_allowlisted(tool: ToolName) -> None:
    """Raise ToolNotAllowlisted if the LLM proposed a tool outside the allowlist."""
    if tool not in ALLOWED_TOOLS:
        log.warning("agent.tool_not_allowlisted", tool=str(tool))
        raise ToolNotAllowlisted(f"{tool} is not in the agent allowlist")


async def validate_proposal(state: AgentState) -> AgentState:
    """Node 3: Validate LLM-proposed tool calls against allowlist and Pydantic models.

    Args:
        state: Current state with ``tool_proposals`` from Node 2.

    Returns:
        Updated state with validated ``tool_proposals`` (invalid ones removed).
    """
    log.info("agent.validate_proposal.start", request_id=state["request_id"])

    validated = []
    for proposal in state.get("tool_proposals", []):
        tool_name_str = proposal.get("name", "")

        # Validate tool name against ToolName enum
        try:
            tool_name = ToolName(tool_name_str)
        except ValueError:
            log.warning("agent.validate.unknown_tool", tool=tool_name_str)
            continue

        # Validate against allowlist (defense-in-depth)
        try:
            assert_tool_allowlisted(tool_name)
        except ToolNotAllowlisted:
            continue

        # Build typed ToolCallProposal
        risk = risk_level_for(tool_name)
        tcp = ToolCallProposal(
            request_id=UUID(state["request_id"]),
            tool_name=tool_name,
            arguments=proposal.get("arguments", {}),
            risk_level=risk,
            rationale=proposal.get("rationale", ""),
            expires_at=datetime.now(UTC) + CONFIRMATION_TTL if risk != RiskLevel.READ else None,
        )
        validated.append(tcp)
        await _mark_scanned_if_possible(tcp)

    state["tool_proposals"] = validated
    log.info("agent.validate_proposal.complete", validated_count=len(validated))
    return state


# =============================================================================
# Node 4: HITL Gate
# =============================================================================


async def hitl_gate(state: AgentState) -> AgentState:
    """Node 4: Check if any tool proposals require human-in-the-loop confirmation.

    Write operations (soft_write, hard_write) are held for user confirmation.
    Read operations pass through to execution.

    Args:
        state: Current state with validated ``tool_proposals``.

    Returns:
        Updated state with ``pending_confirmation`` if writes are present,
        or proposals split into executable reads vs pending writes.
    """
    log.info("agent.hitl_gate.start", request_id=state["request_id"])

    proposals: list[ToolCallProposal] = state.get("tool_proposals", [])

    read_proposals = [p for p in proposals if not p.is_write]
    write_proposals = [p for p in proposals if p.is_write]

    # Execute reads immediately; hold writes for confirmation
    state["tool_proposals"] = read_proposals

    if write_proposals:
        # Return the first write proposal as pending_confirmation
        pending = write_proposals[0]
        state["pending_confirmation"] = pending.model_dump(mode="json")
        await _mark_suggested_if_possible(pending)
        log.info(
            "agent.hitl_gate.confirmation_required",
            tool=str(pending.tool_name),
            risk=str(pending.risk_level),
            proposal_id=str(pending.proposal_id),
        )

    log.info(
        "agent.hitl_gate.complete",
        reads=len(read_proposals),
        writes=len(write_proposals),
    )
    return state


async def _mark_scanned_if_possible(proposal: ToolCallProposal) -> None:
    fqn = _extract_entity_fqn(proposal.arguments)
    if not fqn:
        return
    try:
        await governance_store.transition(
            fqn,
            GovernanceState.SCANNED,
            evidence=f"validated:{proposal.tool_name}",
        )
    except governance_store.GovernanceTransitionError:
        log.debug("agent.governance.scanned.skip", fqn=fqn)


async def _mark_suggested_if_possible(proposal: ToolCallProposal) -> None:
    fqn = _extract_entity_fqn(proposal.arguments)
    if not fqn:
        return
    try:
        await governance_store.transition(
            fqn,
            GovernanceState.SUGGESTED,
            evidence=f"pending_confirmation:{proposal.tool_name}",
        )
    except governance_store.GovernanceTransitionError:
        log.debug("agent.governance.suggested.skip", fqn=fqn)


def _extract_entity_fqn(arguments: dict[str, Any]) -> str | None:
    for key in ("entityFqn", "entity_fqn", "fqn", "fullyQualifiedName"):
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


# =============================================================================
# Node 5: Execute Tool
# =============================================================================


async def execute_tool(state: AgentState) -> AgentState:
    """Node 5: Execute validated read tool proposals against OM MCP server.

    Args:
        state: Current state with read-only ``tool_proposals`` to execute.

    Returns:
        Updated state with ``tool_results`` and ``tool_records`` populated.
    """
    log.info("agent.execute_tool.start", request_id=state["request_id"])

    proposals: list[ToolCallProposal] = state.get("tool_proposals", [])
    results: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for proposal in proposals:
        start = datetime.now(UTC)
        record = ToolCallRecord(
            proposal_id=proposal.proposal_id,
            request_id=proposal.request_id,
            tool_name=proposal.tool_name,
            arguments_redacted=redact_tool_arguments(proposal.arguments),
            confirmed_by_user=False,
            started_at=start,
        )

        try:
            result = await asyncio.to_thread(
                om_mcp.call_tool, str(proposal.tool_name), proposal.arguments
            )
            end = datetime.now(UTC)
            record.completed_at = end
            record.duration_ms = int((end - start).total_seconds() * 1000)
            record.success = True
            record.response_summary = summarize_tool_result(result)
            results.append(result)

        except McpAuthFailed as exc:
            end = datetime.now(UTC)
            record.completed_at = end
            record.duration_ms = int((end - start).total_seconds() * 1000)
            record.success = False
            record.error_code = "om_auth_failed"
            log.warning(
                "agent.execute_tool.failed",
                tool=str(proposal.tool_name),
                error=str(exc),
            )
            results.append({"error": str(exc)})

        except McpUnavailable as exc:
            end = datetime.now(UTC)
            record.completed_at = end
            record.duration_ms = int((end - start).total_seconds() * 1000)
            record.success = False
            record.error_code = "om_unavailable"
            log.warning(
                "agent.execute_tool.failed",
                tool=str(proposal.tool_name),
                error=str(exc),
            )
            results.append({"error": str(exc)})

        except Exception as exc:
            end = datetime.now(UTC)
            record.completed_at = end
            record.duration_ms = int((end - start).total_seconds() * 1000)
            record.success = False
            record.error_code = "internal_error"
            log.exception(
                "agent.execute_tool.failed",
                tool=str(proposal.tool_name),
                error=str(exc),
            )
            results.append({"error": "Internal error executing tool"})

        records.append(record.model_dump(mode="json"))

    state["tool_results"] = results
    state["tool_records"] = records
    log.info("agent.execute_tool.complete", executed=len(results))
    return state


# =============================================================================
# Node 6: Format Response
# =============================================================================

_FORMAT_SYSTEM_PROMPT = """You are a helpful OpenMetadata governance assistant.

Given the tool execution results and the user's original question, provide a clear,
well-formatted response in Markdown.

Rules:
- Use tables for tabular data
- Use bullet points for lists
- Be concise but informative
- If results are empty, say so clearly
- Never expose internal tool names, raw JSON, or error details to the user
- If there's a pending confirmation needed, mention it clearly
"""


async def format_response(state: AgentState) -> AgentState:
    """Node 6: Use LLM to generate a human-readable response from tool results.

    Args:
        state: Current state with ``tool_results`` and optional ``pending_confirmation``.

    Returns:
        Updated state with ``final_response`` as formatted Markdown.
    """
    log.info("agent.format_response.start", request_id=state["request_id"])

    # Build context for the formatter
    context_parts = [f"User question: {state['user_message']}"]
    context_parts.append(f"Classified intent: {state.get('intent', 'unknown')}")

    results = state.get("tool_results", [])
    if results:
        context_parts.append(f"Tool results ({len(results)} calls):")
        for i, result in enumerate(results):
            context_parts.append(f"Result {i + 1}: {json.dumps(result, default=str)[:2000]}")

    pending = state.get("pending_confirmation")
    if pending:
        context_parts.append(
            f"\nIMPORTANT: A write operation is pending confirmation:\n"
            f"Tool: {pending.get('tool_name', 'unknown')}\n"
            f"Risk: {pending.get('risk_level', 'unknown')}\n"
            f"Tell the user they need to confirm this operation."
        )

    try:
        result = await openai_client.call_chat(
            messages=[
                {"role": "system", "content": _FORMAT_SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(context_parts)},
            ],
            max_tokens=1500,
        )
        state["final_response"] = result["content"]
        state["tokens_prompt"] += result["tokens_prompt"]
        state["tokens_completion"] += result["tokens_completion"]

    except (LlmUnavailable, LlmInvalidOutput) as exc:
        log.warning("agent.format_response.failed", error=str(exc))
        # Fallback: raw results as markdown
        if results:
            state["final_response"] = _fallback_format(results, pending)
        else:
            state["final_response"] = "I wasn't able to process your request. Please try again."

    log.info("agent.format_response.complete", request_id=state["request_id"])
    return state


# =============================================================================
# Graph Builder
# =============================================================================


def _should_execute(state: AgentState) -> Literal["execute_tool", "format_response"]:
    """Conditional edge: skip execution if no tool proposals remain (all writes)."""
    proposals = state.get("tool_proposals", [])
    if proposals:
        return "execute_tool"
    return "format_response"


def build_graph() -> StateGraph:
    """Build the LangGraph state machine for one chat turn.

    Returns:
        A compiled ``StateGraph`` ready to be invoked with ``graph.ainvoke(state)``.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("select_tools", select_tools)
    graph.add_node("validate_proposal", validate_proposal)
    graph.add_node("hitl_gate", hitl_gate)
    graph.add_node("execute_tool", execute_tool)
    graph.add_node("format_response", format_response)

    # Wire edges
    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "select_tools")
    graph.add_edge("select_tools", "validate_proposal")
    graph.add_edge("validate_proposal", "hitl_gate")

    # Conditional: if there are read proposals, execute them; otherwise skip to format
    graph.add_conditional_edges(
        "hitl_gate",
        _should_execute,
        {
            "execute_tool": "execute_tool",
            "format_response": "format_response",
        },
    )
    graph.add_edge("execute_tool", "format_response")
    graph.add_edge("format_response", END)

    return graph


# Compiled graph singleton (built once, reused across requests)
_compiled_graph: Any = None


def _get_compiled_graph() -> Any:
    """Return a lazily compiled graph instance."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
    return _compiled_graph


# =============================================================================
# Public API
# =============================================================================


async def run_chat_turn(
    user_message: str,
    session_id: str | None = None,
    request_id: UUID | str | None = None,
) -> dict[str, Any]:
    """Execute one chat turn through the full agent pipeline.

    Args:
        user_message: The user's natural-language message.
        session_id: Optional session ID for continuity.
        request_id: Optional HTTP request ID to preserve end-to-end tracing.

    Returns:
        Dict with keys: ``request_id``, ``session_id``, ``response``,
        ``response_format``, ``pending_confirmation``, ``audit_log``,
        ``tokens_used``, ``ts``.
    """
    log.info(
        "agent.run_chat_turn.start",
        session_id=session_id,
        request_id=str(request_id) if request_id else None,
    )

    state = _initial_state(user_message, session_id, request_id=request_id)
    graph = _get_compiled_graph()
    final_state = await graph.ainvoke(state)

    # Build the API response shape per APIContract.md
    response: dict[str, Any] = {
        "request_id": final_state["request_id"],
        "session_id": final_state["session_id"],
        "response": final_state.get("final_response", ""),
        "response_format": "markdown",
        "audit_log": [
            {
                "tool_name": r.get("tool_name", ""),
                "duration_ms": r.get("duration_ms"),
                "success": r.get("success"),
                "error_code": r.get("error_code"),
            }
            for r in final_state.get("tool_records", [])
        ],
        "tokens_used": {
            "prompt": final_state.get("tokens_prompt", 0),
            "completion": final_state.get("tokens_completion", 0),
        },
        "ts": datetime.now(UTC).isoformat(),
    }

    pending = final_state.get("pending_confirmation")
    if pending:
        response["pending_confirmation"] = pending
        tcp = ToolCallProposal.model_validate(pending)
        await set_pending(UUID(final_state["session_id"]), tcp)

    log.info("agent.run_chat_turn.complete", request_id=final_state["request_id"])
    return response


# =============================================================================
# Helpers
# =============================================================================


def _fallback_format(
    results: list[dict[str, Any]],
    pending: dict[str, Any] | None,
) -> str:
    """Generate a basic markdown response when the LLM formatter is unavailable."""
    parts = ["Here are the results:\n"]
    for i, result in enumerate(results):
        parts.append(
            f"**Result {i + 1}:**\n```json\n{json.dumps(result, indent=2, default=str)[:500]}\n```\n"
        )

    if pending:
        parts.append(
            f"\n⚠️ **Action Required**: A `{pending.get('tool_name', 'write')}` "
            f"operation requires your confirmation."
        )

    return "\n".join(parts)
