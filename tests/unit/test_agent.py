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
"""Unit tests for copilot.services.agent — LangGraph agent orchestrator.

Tests mock the LLM and MCP clients and verify:
- Intent classification
- Tool allowlist enforcement
- HITL gate for write tools
- Read tool direct execution
- Response formatting
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from copilot.models import RiskLevel, ToolCallProposal, ToolName
from copilot.services.agent import (
    ALLOWED_TOOLS,
    AgentState,
    _initial_state,
    assert_tool_allowlisted,
    classify_intent,
    execute_tool,
    format_response,
    hitl_gate,
    run_chat_turn,
    validate_proposal,
)


@pytest.fixture
def base_state() -> AgentState:
    """Create a base agent state for testing."""
    return _initial_state("Show me all customer tables", session_id=None)


class TestClassifyIntent:
    """Tests for the classify_intent node."""

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_classifies_search_intent(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM returns search intent for a search query."""
        mock_llm.return_value = {"intent": "search"}

        result = await classify_intent(base_state)

        assert result["intent"] == "search"
        mock_llm.assert_called_once()

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_classifies_classify_intent(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM returns classify intent for a PII classification query."""
        mock_llm.return_value = {"intent": "classify"}
        base_state["user_message"] = "Auto-classify PII columns in customer_db"

        result = await classify_intent(base_state)

        assert result["intent"] == "classify"

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_falls_back_to_search_on_unknown_intent(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """Unknown intent falls back to search gracefully."""
        mock_llm.return_value = {"intent": "unknown_intent_xyz"}

        result = await classify_intent(base_state)

        assert result["intent"] == "search"

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_falls_back_on_llm_failure(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM failure degrades gracefully to search."""
        from copilot.middleware.error_envelope import LlmUnavailable

        mock_llm.side_effect = LlmUnavailable("timeout")

        result = await classify_intent(base_state)

        assert result["intent"] == "search"
        assert result["error"] is not None


class TestSelectTools:
    """Tests for the select_tools node."""

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_returns_tool_proposals_on_success(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM successfully selects tools and populates proposals."""
        from copilot.services.agent import select_tools

        mock_llm.return_value = {
            "tools": [{"name": "search_metadata", "arguments": {"query": "test"}}],
            "rationale": "search to find tables",
        }
        result = await select_tools(base_state)

        proposals = result["tool_proposals"]
        assert len(proposals) == 1
        assert proposals[0]["name"] == "search_metadata"
        assert proposals[0]["arguments"] == {"query": "test"}
        assert proposals[0]["rationale"] == "search to find tables"

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_returns_empty_proposals_on_llm_failure(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM failure results in empty proposals but does not crash."""
        from copilot.middleware.error_envelope import LlmUnavailable
        from copilot.services.agent import select_tools

        mock_llm.side_effect = LlmUnavailable("timeout")

        result = await select_tools(base_state)
        assert result["tool_proposals"] == []

    @patch("copilot.services.agent.openai_client.call_chat_json", new_callable=AsyncMock)
    async def test_classify_intent_uses_deterministic_tool_chain(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        from copilot.services.agent import select_tools

        base_state["intent"] = "classify"
        base_state["user_message"] = "Scan customer_db and classify PII."

        result = await select_tools(base_state)
        proposals = result["tool_proposals"]

        assert [proposal["name"] for proposal in proposals] == [
            "search_metadata",
            "get_entity_details",
            "patch_entity",
        ]
        assert proposals[0]["arguments"]["queryFilter"] == "service:customer_db"
        assert proposals[1]["arguments"]["entityFqn"] == "sample_mysql.default.customer_db.customers"
        assert len(proposals[2]["arguments"]["patch"]) == 3
        assert proposals[2]["arguments"]["approved_tags"] == [
            "sample_mysql.default.customer_db.customers.email:PII.Sensitive",
            "sample_mysql.default.customer_db.customers.phone:PII.Sensitive",
            "sample_mysql.default.customer_db.customers.ssn:PII.Sensitive",
        ]
        mock_llm.assert_not_awaited()


class TestValidateProposal:
    """Tests for the validate_proposal node."""

    async def test_validates_known_tool(self, base_state: AgentState) -> None:
        """Valid tool names pass validation."""
        base_state["tool_proposals"] = [
            {"name": "search_metadata", "arguments": {"query": "test"}, "rationale": "search"},
        ]

        result = await validate_proposal(base_state)
        proposals = result["tool_proposals"]

        assert len(proposals) == 1
        assert isinstance(proposals[0], ToolCallProposal)
        assert proposals[0].tool_name == ToolName.SEARCH_METADATA
        assert proposals[0].risk_level == RiskLevel.READ

    async def test_rejects_unknown_tool(self, base_state: AgentState) -> None:
        """Unknown tool names are silently dropped."""
        base_state["tool_proposals"] = [
            {"name": "drop_database", "arguments": {}, "rationale": "chaos"},
        ]

        result = await validate_proposal(base_state)
        assert len(result["tool_proposals"]) == 0

    async def test_sets_risk_level_for_write_tools(self, base_state: AgentState) -> None:
        """Write tools get appropriate risk_level and expires_at."""
        base_state["tool_proposals"] = [
            {"name": "patch_entity", "arguments": {"fqn": "test"}, "rationale": "tag"},
        ]

        result = await validate_proposal(base_state)
        proposals = result["tool_proposals"]

        assert len(proposals) == 1
        assert proposals[0].risk_level == RiskLevel.HARD_WRITE
        assert proposals[0].expires_at is not None

    @patch("copilot.services.agent.governance_store.transition", new_callable=AsyncMock)
    async def test_marks_scanned_for_entity_proposals(
        self, mock_transition: AsyncMock, base_state: AgentState
    ) -> None:
        base_state["tool_proposals"] = [
            {
                "name": "patch_entity",
                "arguments": {"entityFqn": "svc.db.schema.table", "patch": []},
                "rationale": "tag",
            },
        ]
        await validate_proposal(base_state)
        assert mock_transition.await_count == 1


class TestToolAllowlist:
    """Tests for assert_tool_allowlisted."""

    def test_all_tool_names_are_allowlisted(self) -> None:
        """Every ToolName enum member is in the allowlist."""
        for tool in ToolName:
            assert_tool_allowlisted(tool)  # should not raise

    def test_allowlist_is_frozen(self) -> None:
        """ALLOWED_TOOLS is an immutable frozenset."""
        assert isinstance(ALLOWED_TOOLS, frozenset)
        assert len(ALLOWED_TOOLS) == len(ToolName)


class TestHitlGate:
    """Tests for the hitl_gate node."""

    async def test_read_tools_pass_through(self, base_state: AgentState) -> None:
        """Read-only proposals pass through without pending_confirmation."""
        proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.SEARCH_METADATA,
            arguments={"query": "test"},
            risk_level=RiskLevel.READ,
        )
        base_state["tool_proposals"] = [proposal]

        result = await hitl_gate(base_state)

        assert len(result["tool_proposals"]) == 1
        assert result["pending_confirmation"] is None

    async def test_write_tools_create_pending_confirmation(self, base_state: AgentState) -> None:
        """Write proposals are held as pending_confirmation."""
        proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.PATCH_ENTITY,
            arguments={"fqn": "db.schema.users"},
            risk_level=RiskLevel.HARD_WRITE,
        )
        base_state["tool_proposals"] = [proposal]

        result = await hitl_gate(base_state)

        assert len(result["tool_proposals"]) == 0  # writes removed from executables
        assert result["pending_confirmation"] is not None
        assert result["pending_confirmation"]["tool_name"] == "patch_entity"

    async def test_mixed_read_write_splits_correctly(self, base_state: AgentState) -> None:
        """Mixed proposals: reads execute, writes held."""
        read_proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.SEARCH_METADATA,
            arguments={"query": "test"},
            risk_level=RiskLevel.READ,
        )
        write_proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.PATCH_ENTITY,
            arguments={"fqn": "test"},
            risk_level=RiskLevel.HARD_WRITE,
        )
        base_state["tool_proposals"] = [read_proposal, write_proposal]

        result = await hitl_gate(base_state)

        assert len(result["tool_proposals"]) == 1  # only the read
        assert result["pending_confirmation"] is not None

    @patch("copilot.services.agent.governance_store.transition", new_callable=AsyncMock)
    async def test_marks_suggested_for_write_proposals(
        self, mock_transition: AsyncMock, base_state: AgentState
    ) -> None:
        write_proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.PATCH_ENTITY,
            arguments={"entityFqn": "svc.db.schema.table", "patch": []},
            risk_level=RiskLevel.HARD_WRITE,
        )
        base_state["tool_proposals"] = [write_proposal]
        await hitl_gate(base_state)
        assert mock_transition.await_count == 1


class TestExecuteTool:
    """Tests for the execute_tool node."""

    @patch("copilot.services.agent.om_mcp.call_tool")
    async def test_executes_read_tool_successfully(
        self, mock_call: Any, base_state: AgentState
    ) -> None:
        """Successful read tool returns results and records."""
        mock_call.return_value = {"tables": [{"fqn": "db.users"}]}

        proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.SEARCH_METADATA,
            arguments={"query": "users"},
            risk_level=RiskLevel.READ,
        )
        base_state["tool_proposals"] = [proposal]

        result = await execute_tool(base_state)

        assert len(result["tool_results"]) == 1
        assert result["tool_results"][0] == {"tables": [{"fqn": "db.users"}]}
        assert len(result["tool_records"]) == 1
        assert result["tool_records"][0]["success"] is True

    @patch("copilot.services.agent.om_mcp.call_tool")
    async def test_records_failure_on_mcp_error(
        self, mock_call: Any, base_state: AgentState
    ) -> None:
        """MCP errors are recorded in audit log with success=False."""
        from copilot.middleware.error_envelope import McpUnavailable

        mock_call.side_effect = McpUnavailable("timeout")

        proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.SEARCH_METADATA,
            arguments={"query": "test"},
            risk_level=RiskLevel.READ,
        )
        base_state["tool_proposals"] = [proposal]

        result = await execute_tool(base_state)

        assert result["tool_records"][0]["success"] is False
        assert result["tool_records"][0]["error_code"] == "om_unavailable"

    @patch("copilot.services.agent.asyncio.to_thread", new_callable=AsyncMock)
    async def test_records_failure_on_auth_error(
        self, mock_to_thread: AsyncMock, base_state: AgentState
    ) -> None:
        """MCP auth errors are recorded uniquely with om_auth_failed."""
        from copilot.middleware.error_envelope import McpAuthFailed

        mock_to_thread.side_effect = McpAuthFailed("unauthorized")

        proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.SEARCH_METADATA,
            arguments={"query": "test"},
            risk_level=RiskLevel.READ,
        )
        base_state["tool_proposals"] = [proposal]

        result = await execute_tool(base_state)

        assert len(result["tool_records"]) == 1
        assert result["tool_records"][0]["success"] is False
        assert result["tool_records"][0]["error_code"] == "om_auth_failed"


class TestFormatResponse:
    """Tests for the format_response node."""

    @patch("copilot.services.agent.openai_client.call_chat", new_callable=AsyncMock)
    async def test_formats_response_as_markdown(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM formats tool results into markdown."""
        mock_llm.return_value = {
            "content": "Found **2 tables** matching your query.",
            "tokens_prompt": 100,
            "tokens_completion": 20,
        }
        base_state["tool_results"] = [{"tables": [{"fqn": "db.users"}]}]

        result = await format_response(base_state)

        assert result["final_response"] is not None
        assert "Found **2 tables**" in result["final_response"]
        assert result["tokens_prompt"] == 100

    @patch("copilot.services.agent.openai_client.call_chat", new_callable=AsyncMock)
    async def test_uses_fallback_on_llm_failure(
        self, mock_llm: AsyncMock, base_state: AgentState
    ) -> None:
        """LLM failure produces a fallback response with raw data."""
        from copilot.middleware.error_envelope import LlmUnavailable

        mock_llm.side_effect = LlmUnavailable("timeout")
        base_state["tool_results"] = [{"data": "test"}]

        result = await format_response(base_state)

        assert result["final_response"] is not None
        assert result["final_response"] is not None
        assert "Result 1" in result["final_response"]


class TestRunChatTurn:
    @patch("copilot.services.agent._get_compiled_graph")
    async def test_preserves_supplied_request_id(self, mock_get_graph: Any) -> None:
        """Provided request IDs are preserved through the API response."""
        request_id = uuid4()
        session_id = uuid4()
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "request_id": str(request_id),
            "session_id": str(session_id),
            "final_response": "Done.",
            "tool_records": [],
            "tokens_prompt": 0,
            "tokens_completion": 0,
        }
        mock_get_graph.return_value = mock_graph

        result = await run_chat_turn("show me tables", request_id=request_id)

        assert result["request_id"] == str(request_id)
        assert result["session_id"] == str(session_id)
        mock_graph.ainvoke.assert_awaited_once()
        initial_state = mock_graph.ainvoke.await_args.args[0]
        assert initial_state["request_id"] == str(request_id)

    @patch("copilot.services.agent._get_compiled_graph")
    async def test_audit_log_includes_error_code(self, mock_get_graph: Any) -> None:
        """Failed tool calls surface error_code in the API audit_log."""
        request_id = uuid4()
        session_id = uuid4()
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "request_id": str(request_id),
            "session_id": str(session_id),
            "final_response": "Could not search.",
            "tool_records": [
                {
                    "tool_name": "search_metadata",
                    "duration_ms": 12,
                    "success": False,
                    "error_code": "om_unavailable",
                }
            ],
            "tokens_prompt": 0,
            "tokens_completion": 0,
        }
        mock_get_graph.return_value = mock_graph

        result = await run_chat_turn("show me tables", request_id=request_id)

        assert len(result["audit_log"]) == 1
        assert result["audit_log"][0]["error_code"] == "om_unavailable"
        assert result["audit_log"][0]["success"] is False
