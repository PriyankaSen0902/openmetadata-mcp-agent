# API Contract

> Phase 3.5 deliverable per [Feature-Dev SKILL.md](../../agents/Feature-Dev/SKILL.md). Full FastAPI surface for `openmetadata-mcp-agent`. Request/response shapes, error codes, status codes, auth model. The chat UI and any external client codes against this contract.

## Versioning

- **v1**: this document. Breaking changes bump to `v2`.
- All routes prefixed with `/api/v1/`.

## Auth

| Phase              | Auth on `/api/v1/*`                                                                     | Notes                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **v1 (hackathon)** | None — dev-only, FastAPI binds to `127.0.0.1:8000`                                      | Documented in [Security/ThreatModel.md](../Security/ThreatModel.md). Browser is treated as trusted (single-laptop demo). |
| **v2 (roadmap)**   | OM OAuth callback per [openmetadata-mcp/README.md](../../../openmetadata-mcp/README.md) | Out of scope this round.                                                                                                 |

Outbound auth (agent → external systems): `AI_SDK_TOKEN` (Bot JWT for OM), `OPENAI_API_KEY`, `GITHUB_TOKEN`. See [Security/SecretsHandling.md](../Security/SecretsHandling.md).

## Error envelope

Every non-2xx response uses the shape from [DataModel.md §Error envelope](./DataModel.md):

```json
{
  "code": "snake_case_machine_readable",
  "message": "Human-safe; no secrets, paths, stack traces",
  "request_id": "uuid-v4",
  "ts": "2026-04-26T14:30:00.000+05:30",
  "details": { "optional safe metadata only": "..." }
}
```

## Routes

### `POST /api/v1/chat`

User submits a natural-language message. Agent runs intent classification → tool selection → execution (read tools) or proposal (write tools).

**Request**:

```json
{
  "message": "Auto-classify PII in customer_db",
  "session_id": "uuid-v4 (optional; new session if absent)"
}
```

| Field        | Type   | Required | Constraints                                    |
| ------------ | ------ | -------- | ---------------------------------------------- |
| `message`    | string | yes      | 1..4000 chars; UTF-8; no NUL bytes             |
| `session_id` | UUID   | no       | If absent, server generates one and returns it |

**Response 200 — completed (read-only flow)**:

```json
{
  "request_id": "uuid-v4",
  "session_id": "uuid-v4",
  "response": "Found 12 PII columns across 5 tables...\n\n| Table | Column | Suggested Tag | Confidence |\n|-------|--------|---------------|------------|\n...",
  "response_format": "markdown",
  "audit_log": [
    {
      "tool_name": "search_metadata",
      "duration_ms": 245,
      "success": true
    }
  ],
  "tokens_used": { "prompt": 312, "completion": 187 },
  "ts": "2026-04-26T14:30:00.000+05:30"
}
```

**Response 200 — confirmation required (write flow)**:

```json
{
  "request_id": "uuid-v4",
  "session_id": "uuid-v4",
  "response": "I propose tagging 12 columns as PII.Sensitive across 5 tables. Confirm to apply.",
  "response_format": "markdown",
  "pending_confirmation": {
    "proposal_id": "uuid-v4",
    "tool_name": "patch_entity",
    "risk_level": "hard_write",
    "summary": "Apply PII.Sensitive tag to 12 columns across 5 tables",
    "preview_diff": "[ ... a human-readable diff that the UI renders, NEVER the raw JSON Patch ... ]",
    "expires_at": "2026-04-26T14:35:00.000+05:30"
  },
  "audit_log": [ ... ],
  "ts": "..."
}
```

**As implemented (P2-19 / #75)**: `pending_confirmation` is the JSON serialization of the full `ToolCallProposal` (includes `arguments`, `request_id`, `proposed_at`, `rationale`, etc.). The UI-oriented `summary` and `preview_diff` fields above are aspirational for a richer client; the server does not synthesize them separately yet.

**Response 422 — validation_failed**: request body shape invalid.

**Response 422 — tool_not_allowlisted**: LLM proposed a tool outside the 13-tool allowlist (logged as security event).

**Response 429 — rate_limited**: 30 req/min per IP exceeded.

**Response 429 — llm_token_budget_exceeded**: session hit configured cap.

**Response 502 — om_auth_failed | llm_invalid_output**: upstream returned bad data.

**Response 503 — om_unavailable | llm_unavailable**: circuit breaker open per [NFRs.md §Circuit breakers](../Project/NFRs.md).

**Response 500 — internal_error**: catch-all; logged + alerted.

---

### `POST /api/v1/chat/confirm`

User accepts or rejects a pending write proposal.

**Request**:

```json
{
  "session_id": "uuid-v4",
  "proposal_id": "uuid-v4",
  "accepted": true
}
```

| Field         | Type    | Required |
| ------------- | ------- | -------- |
| `session_id`  | UUID    | yes      |
| `proposal_id` | UUID    | yes      |
| `accepted`    | boolean | yes      |

**Response 200 — accepted=true, executed**:

```json
{
  "request_id": "uuid-v4",
  "session_id": "uuid-v4",
  "response": "Done. Tagged 12 columns as PII.Sensitive across 5 tables in 8.2s.",
  "audit_log": [
    {
      "tool_name": "patch_entity",
      "confirmed_by_user": true,
      "duration_ms": 234,
      "success": true
    }
  ],
  "ts": "..."
}
```

**Response 200 — accepted=false, rejected**:

```json
{
  "request_id": "uuid-v4",
  "session_id": "uuid-v4",
  "response": "Cancelled. No changes were made. Anything else?",
  "audit_log": [],
  "ts": "..."
}
```

**Response 410 — confirmation_expired**: > 5 min elapsed since proposal returned.

**Response 422 — proposal_not_found**: `proposal_id` does not match any pending proposal in the session.

---

### `POST /api/v1/chat/cancel`

User cancels the current chat session (clears state).

**Request**:

```json
{ "session_id": "uuid-v4" }
```

**Response 200**:

```json
{ "session_id": "uuid-v4", "cancelled": true, "ts": "..." }
```

---

### `GET /api/v1/healthz`

Liveness + readiness probe. Returns 200 if the agent process is up and `data-ai-sdk` can ping the OM MCP server.

**Response 200**:

```json
{
  "status": "ok",
  "checks": {
    "om_mcp": { "ok": true, "latency_ms": 42 },
    "openai": { "ok": true, "latency_ms": 180 }
  },
  "version": "0.1.0",
  "ts": "..."
}
```

**Response 503**:

```json
{
  "status": "degraded",
  "checks": {
    "om_mcp": { "ok": false, "error": "om_unavailable" },
    "openai": { "ok": true, "latency_ms": 195 }
  },
  "ts": "..."
}
```

The agent still serves chat requests when degraded (with circuit-breaker-driven graceful errors); the health probe just reports the truth.

---

### `GET /api/v1/metrics`

Prometheus text-format metrics endpoint. Always 200 (text/plain).

**Exposed series** (per [NFRs.md §NFR-06 Observability](../Project/NFRs.md)):

| Metric                          | Type                                  | Labels                                       |
| ------------------------------- | ------------------------------------- | -------------------------------------------- |
| `agent_requests_total`          | counter                               | `endpoint`, `status_code`                    |
| `agent_errors_total`            | counter                               | `code` (matches error envelope `code`)       |
| `agent_request_latency_seconds` | histogram                             | `endpoint`                                   |
| `agent_llm_tokens_used_total`   | counter                               | `direction` (`prompt`/`completion`), `model` |
| `agent_llm_calls_total`         | counter                               | `model`, `outcome` (`ok`/`retry`/`fail`)     |
| `agent_mcp_calls_total`         | counter                               | `tool_name`, `outcome`                       |
| `agent_circuit_breaker_state`   | gauge (0=closed, 1=open, 2=half-open) | `circuit` (`om_mcp`/`openai`/`github_mcp`)   |
| `agent_pending_confirmations`   | gauge                                 | —                                            |
| `agent_active_sessions`         | gauge                                 | —                                            |

---

### `GET /api/v1/governance/drift`

Returns the latest governance drift scan results. The drift worker runs in the FastAPI lifespan on a configurable interval (`DRIFT_POLL_INTERVAL_SECONDS`, default 60s) and caches results in memory.

**Response 200 — drift findings**:

```json
{
  "drift": [
    {
      "entity_fqn": "customer_db.public.customers",
      "entity_type": "table",
      "signal": "hash_changed",
      "detail": "Entity hash changed from a1b2c3d4e5f6… to f6e5d4c3b2a1…",
      "detected_at": "2026-04-26T14:30:00.000+05:30"
    },
    {
      "entity_fqn": "customer_db.public.customers",
      "entity_type": "table",
      "signal": "tag_missing",
      "detail": "Governance tag 'PII.Sensitive' was removed",
      "detected_at": "2026-04-26T14:30:00.000+05:30"
    }
  ],
  "scanned_at": "2026-04-26T14:30:00.000+05:30",
  "entity_count": 42,
  "drift_count": 2,
  "ts": "2026-04-26T14:30:01.000+05:30"
}
```

| Field          | Type   | Description                               |
| -------------- | ------ | ----------------------------------------- |
| `drift`        | array  | List of drift findings                    |
| `scanned_at`   | string | ISO-8601 timestamp of last scan           |
| `entity_count` | int    | Number of entities scanned                |
| `drift_count`  | int    | Number of drift findings                  |
| `ts`           | string | Response timestamp                        |

**Drift signals**: `hash_changed`, `tag_missing`, `tag_unexpected`.

**Response 503 — om_unavailable**: OM MCP was unreachable during the last scan. Returns the standard error envelope.

---

## Conventions

- **Content-Type**: `application/json` for all JSON requests/responses.
- **Time format**: ISO 8601 with timezone (`2026-04-26T14:30:00.000+05:30`). Server side produces; never accept naive timestamps.
- **UUIDs**: v4, lowercase, hyphenated.
- **UI session continuity**: browser clients persist `session_id` from each `/chat` response and send it back on subsequent `/chat` requests.
- **Markdown in `response`**: limited subset — headings, bold/italic, lists, tables, inline code. NO raw HTML, NO `<script>`, NO `javascript:` URLs (UI renders with `react-markdown` + `rehype-sanitize`).
- **`details` in error envelope**: must be a flat object with safe types (string, number, bool, array of those). NEVER a Pydantic model dump that could include secrets.
- **Error UX**: clients must surface envelope `code` + canonical `message`; never render raw exception strings or stack traces.

## What this contract is NOT

- Not stable across major versions — `v2` may rename fields.
- Not authenticated in v1 — bind to loopback only ([Security/ThreatModel.md](../Security/ThreatModel.md)).
- Not idempotent for write proposals — `proposal_id` is single-use; once executed or expired, it cannot be re-confirmed.

## OpenAPI

FastAPI auto-generates `/api/v1/openapi.json` and a Swagger UI at `/api/v1/docs`. Both are enabled in v1 (judges can hit them live during the demo per [JudgePersona.md §Moment 2](../Project/JudgePersona.md)).
