# Data Model

> Phase 3.4 deliverable per [Feature-Dev SKILL.md](../../agents/Feature-Dev/SKILL.md).
>
> The agent has no database for v1 (per [NFRs.md §NFR-05](../Project/NFRs.md)). All state is in-memory Pydantic objects, scoped to a single FastAPI process, lost on restart. This doc is the contract for future persistence work and the source of truth for shape consistency between the API layer, the LangGraph state, and the audit log.

## Pydantic models (canonical shapes)

### `ChatSession`

Per `request_id`. Lives only in the LangGraph state graph; not persisted.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class ChatSession(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    started_at: datetime
    user_message: str
    intent: Literal["search", "classify", "lineage", "rca", "glossary", "metric", "test", "multi_mcp"] | None = None
    tool_calls: list["ToolCallRecord"] = []
    pending_confirmation: "ToolCallProposal | None" = None
    final_response: str | None = None
```

### `ToolCallProposal`

What the LLM proposed but has not yet been executed. Subject to validation + HITL gate.

```python
class ToolCallProposal(BaseModel):
    """LLM-suggested tool call awaiting validation + (for writes) user confirmation."""
    proposal_id: UUID = Field(default_factory=uuid4)
    request_id: UUID                                  # parent ChatSession
    tool_name: Literal[
        # 7 typed enum tools
        "search_metadata", "get_entity_details", "get_entity_lineage",
        "create_glossary", "create_glossary_term", "create_lineage", "patch_entity",
        # 5 string-callable tools
        "semantic_search", "get_test_definitions", "create_test_case",
        "create_metric", "root_cause_analysis",
        # GitHub MCP (Phase 3 only; allowlisted)
        "github_create_issue",
    ]
    arguments: dict[str, Any]                         # validated against MCP tool schema before this object is constructed
    is_write: bool                                    # True = requires HITL confirmation
    risk_level: Literal["read", "soft_write", "hard_write"]
    rationale: str                                    # LLM's stated reason; capped at 500 chars
    proposed_at: datetime
```

`risk_level` rules:

| Tool                                                                                                                            | risk_level                                          |
| ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `search_metadata`, `semantic_search`, `get_entity_details`, `get_entity_lineage`, `get_test_definitions`, `root_cause_analysis` | `read`                                              |
| `create_glossary`, `create_glossary_term`, `create_metric`, `create_test_case`, `create_lineage`                                | `soft_write` (creates new, doesn't mutate existing) |
| `patch_entity`, `github_create_issue`                                                                                           | `hard_write` (mutates existing or external system)  |

`hard_write` ALWAYS requires user confirmation in the UI before execution. `soft_write` requires confirmation in v1 (we may relax in v2 with policy rules). `read` executes without prompt.

### `ToolCallRecord`

Append-only entry for the audit log. One per executed tool call.

```python
class ToolCallRecord(BaseModel):
    proposal_id: UUID
    request_id: UUID
    tool_name: str
    arguments_redacted: dict[str, Any]                # secrets stripped, large fields truncated to 200 chars
    confirmed_by_user: bool                           # False for read tools; True for write tools (gate enforced)
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    success: bool | None = None
    error_code: str | None = None                     # matches NFRs.md error envelope
    response_summary: str                             # max 500 chars — never the raw response
```

### `ClassificationJob`

Auto-classification flow state ([FeatureDev/AutoClassification.md](../FeatureDev/AutoClassification.md)).

```python
class ClassificationJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    target_filter: dict[str, Any]                     # the search_metadata query (e.g. {"entityType":"table","queryFilter":...})
    tables_scanned: int = 0
    columns_inspected: int = 0
    suggestions: list["TagSuggestion"] = []
    status: Literal["scanning", "awaiting_confirmation", "applying", "done", "failed"]
    started_at: datetime
    finished_at: datetime | None = None

class TagSuggestion(BaseModel):
    table_fqn: str
    column_name: str
    suggested_tag: str                                # e.g. "PII.Sensitive"
    confidence: float = Field(ge=0.0, le=1.0)         # LLM-reported; >= 0.7 to surface
    reason: str                                       # max 200 chars; ESCAPED from prompt-injection
    accepted: bool | None = None                      # filled by user in UI
```

### `LineageImpactReport`

Output of the lineage impact workflow ([FeatureDev/LineageImpact.md](../FeatureDev/LineageImpact.md)).

```python
class LineageImpactReport(BaseModel):
    root_fqn: str
    root_entity_type: str
    upstream: list["LineageNode"]
    downstream: list["LineageNode"]
    critical_assets_at_risk: list[str]                # FQNs tagged Tier.Tier1 in the downstream
    summary_markdown: str                             # human-readable; what the chat UI renders

class LineageNode(BaseModel):
    fqn: str
    entity_type: str
    tier: str | None = None
    owners: list[str] = []
    hops_from_root: int
```

### Error envelope

Every API error response uses this shape (per [NFRs.md §The 5 Things AI Never Adds — Structured errors](../Project/NFRs.md)):

```python
class ErrorEnvelope(BaseModel):
    code: str                                         # snake_case machine-readable
    message: str                                      # human-readable, safe to render
    request_id: UUID
    ts: datetime
    details: dict[str, Any] | None = None             # safe metadata only; never secrets, paths, raw exceptions
```

Standard `code` values (extend with care):

| Code                        | Meaning                                           | HTTP status                              |
| --------------------------- | ------------------------------------------------- | ---------------------------------------- |
| `validation_failed`         | Request body shape wrong                          | 422                                      |
| `tool_not_allowlisted`      | LLM proposed a tool outside the 13-tool allowlist | 422                                      |
| `confirmation_required`     | Write tool needs user confirmation                | 200 (returned in `pending_confirmation`) |
| `confirmation_expired`      | User took > 5 min to confirm                      | 410                                      |
| `om_unavailable`            | OM MCP circuit breaker open                       | 503                                      |
| `om_auth_failed`            | Bot JWT invalid/expired                           | 502                                      |
| `llm_unavailable`           | OpenAI circuit breaker open                       | 503                                      |
| `llm_invalid_output`        | Pydantic validation failed on LLM JSON            | 502                                      |
| `llm_token_budget_exceeded` | Session hit max tokens                            | 429                                      |
| `rate_limited`              | slowapi gate triggered                            | 429                                      |
| `internal_error`            | Catch-all unhandled exception (logged + alerted)  | 500                                      |

## Data flow (model objects through the system)

```
[POST /chat with user_message]
    -> ChatSession created (in LangGraph state)
        -> Agent loop:
            -> LLM proposes tool call
            -> Pydantic validates args -> ToolCallProposal
            -> if risk_level == "read": execute, append ToolCallRecord
            -> if risk_level in {soft_write, hard_write}:
                  -> store ToolCallProposal in session.pending_confirmation
                  -> return 200 with confirmation_required envelope
                  -> [POST /chat/confirm with proposal_id + accepted=true|false]
                  -> if accepted: execute, append ToolCallRecord
                  -> if not: append rejection record, agent re-plans
        -> Agent constructs final_response (markdown)
    -> 200 response: {request_id, response, audit_log: [ToolCallRecord, ...]}
```

## State persistence boundaries (v1 in-memory)

| Store                               | What's in it                                                                 | Lifetime                       |
| ----------------------------------- | ---------------------------------------------------------------------------- | ------------------------------ |
| LangGraph in-memory checkpointer    | `ChatSession`, `ToolCallProposal` (pending), `ClassificationJob` (in-flight) | Until process restart          |
| In-memory cache (per process, dict) | OM tool list (`client.mcp.list_tools()` result, refreshed every 60s)         | Until process restart          |
| `logs/agent.log`                    | `ToolCallRecord` entries serialized as JSON lines                            | 5 rotating files of 10 MB each |
| `seed/customer_db.json`             | The 50+ table fixture for the demo                                           | Repo-pinned                    |

## What we explicitly do NOT model in v1

- User identity (FastAPI `/chat` is dev-only, single-user, no auth)
- Multi-tenant catalog separation (out of scope per [Discovery.md](../Project/Discovery.md))
- Persistent classification policies (every job is one-shot)
- Cost accounting per session beyond the in-memory token counter
- A real RBAC layer (the agent inherits the Bot user's OM permissions; that's the entire authz story)

These are documented as out-of-scope so reviewers don't add them silently.
