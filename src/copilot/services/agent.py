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
"""LangGraph agent orchestrator. Stubbed in Phase 1; implemented in Phase 2.

Per .idea/Plan/Architecture/AgentPipeline.md: classify intent -> tool select
-> validate -> (if write) HITL gate -> execute -> format response. Each step
is a node in the LangGraph state machine.

Module G defense Layer 4: ALLOWED_TOOLS is the tool allowlist that the LLM
is constrained to. Anything outside raises ToolNotAllowlisted (HTTP 422).
"""

from __future__ import annotations

from copilot.middleware.error_envelope import ToolNotAllowlisted
from copilot.models import ToolCallProposal, ToolName
from copilot.observability import get_logger

log = get_logger(__name__)

# Module G Layer 4: server-side allowlist enforcement (defense-in-depth even
# though the Pydantic Literal type already constrains this).
ALLOWED_TOOLS: frozenset[ToolName] = frozenset(ToolName)


def assert_tool_allowlisted(tool: ToolName) -> None:
    """Raise ToolNotAllowlisted if the LLM proposed a tool outside the allowlist."""
    if tool not in ALLOWED_TOOLS:
        log.warning("agent.tool_not_allowlisted", tool=str(tool))
        raise ToolNotAllowlisted(f"{tool} is not in the agent allowlist")


# TODO P2-04: build the LangGraph state machine.
# Nodes (per .idea/Plan/Architecture/AgentPipeline.md):
#   1. classify_intent (LLM)
#   2. select_tool    (LLM)
#   3. validate       (Pydantic)
#   4. hitl_gate      (returns pending_confirmation if write)
#   5. execute_tool   (call clients/om_mcp.py or clients/openai_client.py)
#   6. format_response (LLM)


async def run_chat_turn(
    user_message: str,
    session_id: str | None = None,
) -> ToolCallProposal:
    """Execute one chat turn. Stubbed in Phase 1; implement in P2-04.

    Returns a ToolCallProposal for the chat layer to act on (execute if read,
    gate-then-execute if write).
    """
    log.warning("agent.run_chat_turn.not_implemented", session_id=session_id)
    raise NotImplementedError("agent.run_chat_turn implementation pending (P2-04)")
