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
"""Chat session, tool-call, and audit-log Pydantic models.

Exact shapes per .idea/Plan/Architecture/DataModel.md. Single source of truth
for what crosses any layer boundary in this app.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ToolName(StrEnum):
    """Allowlist of MCP tools the LLM may propose. Anything outside is rejected.

    7 typed (per `data-ai-sdk` MCPTool enum) + 5 string-callable (via
    `client.mcp.call_tool(name, args)`) + 1 GitHub MCP (Phase 3).
    """

    # ---- 7 typed via data-ai-sdk MCPTool enum ----
    SEARCH_METADATA = "search_metadata"
    GET_ENTITY_DETAILS = "get_entity_details"
    GET_ENTITY_LINEAGE = "get_entity_lineage"
    CREATE_GLOSSARY = "create_glossary"
    CREATE_GLOSSARY_TERM = "create_glossary_term"
    CREATE_LINEAGE = "create_lineage"
    PATCH_ENTITY = "patch_entity"

    # ---- 5 string-callable via call_tool() ----
    SEMANTIC_SEARCH = "semantic_search"
    GET_TEST_DEFINITIONS = "get_test_definitions"
    CREATE_TEST_CASE = "create_test_case"
    CREATE_METRIC = "create_metric"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"

    # ---- Phase 3 GitHub MCP ----
    GITHUB_CREATE_ISSUE = "github_create_issue"


class RiskLevel(StrEnum):
    """Per ToolCallProposal: drives whether HITL confirmation gate fires."""

    READ = "read"
    SOFT_WRITE = "soft_write"
    HARD_WRITE = "hard_write"


# ---- Risk-level mapping (single source of truth) ----
_TOOL_RISK: dict[ToolName, RiskLevel] = {
    ToolName.SEARCH_METADATA: RiskLevel.READ,
    ToolName.SEMANTIC_SEARCH: RiskLevel.READ,
    ToolName.GET_ENTITY_DETAILS: RiskLevel.READ,
    ToolName.GET_ENTITY_LINEAGE: RiskLevel.READ,
    ToolName.GET_TEST_DEFINITIONS: RiskLevel.READ,
    ToolName.ROOT_CAUSE_ANALYSIS: RiskLevel.READ,
    ToolName.CREATE_GLOSSARY: RiskLevel.SOFT_WRITE,
    ToolName.CREATE_GLOSSARY_TERM: RiskLevel.SOFT_WRITE,
    ToolName.CREATE_METRIC: RiskLevel.SOFT_WRITE,
    ToolName.CREATE_TEST_CASE: RiskLevel.SOFT_WRITE,
    ToolName.CREATE_LINEAGE: RiskLevel.SOFT_WRITE,
    ToolName.PATCH_ENTITY: RiskLevel.HARD_WRITE,
    ToolName.GITHUB_CREATE_ISSUE: RiskLevel.HARD_WRITE,
}


def risk_level_for(tool: ToolName) -> RiskLevel:
    """Return the risk level for a given tool. Single source of truth."""
    return _TOOL_RISK[tool]


def _now_utc() -> datetime:
    return datetime.now(UTC)


# =============================================================================
# Chat session
# =============================================================================


class ChatSession(BaseModel):
    """Per-request_id session held in LangGraph state. Not persisted in v1."""

    model_config = ConfigDict(frozen=False)

    request_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(default_factory=_now_utc)
    user_message: str = Field(min_length=1, max_length=4000)
    intent: (
        Literal["search", "classify", "lineage", "rca", "glossary", "metric", "test", "multi_mcp"]
        | None
    ) = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    pending_confirmation: ToolCallProposal | None = None
    final_response: str | None = None
    tokens_used_prompt: int = 0
    tokens_used_completion: int = 0


# =============================================================================
# Tool call proposal + record
# =============================================================================


class ToolCallProposal(BaseModel):
    """LLM-suggested tool call awaiting validation + (for writes) HITL gate."""

    model_config = ConfigDict(frozen=False)

    proposal_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    tool_name: ToolName
    arguments: dict[str, Any]
    risk_level: RiskLevel
    rationale: str = Field(default="", max_length=500)
    proposed_at: datetime = Field(default_factory=_now_utc)
    expires_at: datetime | None = None  # set by service layer (5 min TTL)

    @property
    def is_write(self) -> bool:
        return self.risk_level is not RiskLevel.READ


class PendingSession(BaseModel):
    """In-memory session row for HITL confirm/cancel (P2-19). Not persisted across restart."""

    model_config = ConfigDict(frozen=False)

    session_id: UUID
    pending: ToolCallProposal | None = None
    expires_at: datetime | None = None
    updated_at: datetime = Field(default_factory=_now_utc)


class ToolCallRecord(BaseModel):
    """Append-only audit-log entry. One per executed tool call."""

    model_config = ConfigDict(frozen=False)

    proposal_id: UUID
    request_id: UUID
    tool_name: ToolName
    arguments_redacted: dict[str, Any]
    confirmed_by_user: bool = False
    started_at: datetime = Field(default_factory=_now_utc)
    completed_at: datetime | None = None
    duration_ms: int | None = None
    success: bool | None = None
    error_code: str | None = None
    response_summary: str = Field(default="", max_length=500)


# =============================================================================
# Auto-classification flow models
# =============================================================================


class TagSuggestion(BaseModel):
    """One LLM-suggested tag for one column. Only confidence>=0.7 is surfaced."""

    table_fqn: str
    column_name: str
    suggested_tag: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(default="", max_length=200)
    accepted: bool | None = None
    suspicious: bool = False  # True if column had instruction-injection pattern


class ClassificationJob(BaseModel):
    """Auto-classification flow state."""

    model_config = ConfigDict(frozen=False)

    job_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    target_filter: dict[str, Any]
    tables_scanned: int = 0
    columns_inspected: int = 0
    suggestions: list[TagSuggestion] = Field(default_factory=list)
    status: Literal["scanning", "awaiting_confirmation", "applying", "done", "failed"] = "scanning"
    started_at: datetime = Field(default_factory=_now_utc)
    finished_at: datetime | None = None


# =============================================================================
# Lineage impact models
# =============================================================================


class LineageNode(BaseModel):
    fqn: str
    entity_type: str
    tier: str | None = None
    owners: list[str] = Field(default_factory=list)
    hops_from_root: int = Field(ge=0)


class LineageImpactReport(BaseModel):
    root_fqn: str
    root_entity_type: str
    upstream: list[LineageNode] = Field(default_factory=list)
    downstream: list[LineageNode] = Field(default_factory=list)
    critical_assets_at_risk: list[str] = Field(default_factory=list)
    summary_markdown: str = ""


# =============================================================================
# Error envelope (per .idea/Plan/Architecture/APIContract.md)
# =============================================================================


class ErrorCode(StrEnum):
    """Canonical error codes. Extend with care; API contract."""

    VALIDATION_FAILED = "validation_failed"
    TOOL_NOT_ALLOWLISTED = "tool_not_allowlisted"
    CONFIRMATION_REQUIRED = "confirmation_required"
    CONFIRMATION_EXPIRED = "confirmation_expired"
    PROPOSAL_NOT_FOUND = "proposal_not_found"
    OM_UNAVAILABLE = "om_unavailable"
    OM_AUTH_FAILED = "om_auth_failed"
    LLM_UNAVAILABLE = "llm_unavailable"
    LLM_INVALID_OUTPUT = "llm_invalid_output"
    LLM_TOKEN_BUDGET_EXCEEDED = "llm_token_budget_exceeded"
    GITHUB_UNAVAILABLE = "github_unavailable"
    RATE_LIMITED = "rate_limited"
    NOT_IMPLEMENTED = "not_implemented"
    INTERNAL_ERROR = "internal_error"


class ErrorEnvelope(BaseModel):
    """Canonical error response shape. NEVER includes secrets/paths/raw exceptions."""

    code: ErrorCode
    message: str = Field(max_length=500)
    request_id: UUID
    ts: datetime = Field(default_factory=_now_utc)
    details: dict[str, Any] | None = None


# Resolve forward references
ChatSession.model_rebuild()
