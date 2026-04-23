# API Reference

Live, auto-generated Swagger UI: http://127.0.0.1:8000/api/v1/docs (when the agent is running)
Auto-generated OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json

This page summarizes the surface; for request/response field details see Swagger or [`.idea/Plan/Architecture/APIContract.md`](../.idea/Plan/Architecture/APIContract.md).

## Versioning

All routes prefixed with `/api/v1/`. Breaking changes bump to `v2`.

## Auth (v1)

None on FastAPI ingress — the backend binds to `127.0.0.1:8000` only (loopback). v2 will add OpenMetadata OAuth callback for per-user impersonation.

## Routes

### `POST /api/v1/chat`

Submit a natural-language message. Agent classifies intent, picks the right MCP tool(s), executes (read tools) or proposes (write tools).

Request:

```json
{
  "message": "Auto-classify PII in customer_db",
  "session_id": "uuid-v4 (optional; new session if absent)"
}
```

Response 200 (read-only flow completed):

```json
{
  "request_id": "uuid",
  "session_id": "uuid",
  "response": "Found 12 PII candidates ...",
  "response_format": "markdown",
  "audit_log": [
    {
      "tool_name": "search_metadata",
      "duration_ms": 245,
      "success": true,
      "error_code": null
    }
  ],
  "tokens_used": { "prompt": 312, "completion": 187 },
  "ts": "2026-04-26T14:30:00.000+05:30"
}
```

For the same call, the JSON `request_id` matches the `X-Request-Id` response header.

Response 200 (write flow needs confirmation):

```json
{
  "request_id": "uuid",
  "session_id": "uuid",
  "response": "I propose tagging 12 columns ...",
  "pending_confirmation": {
    "proposal_id": "uuid",
    "tool_name": "patch_entity",
    "risk_level": "hard_write",
    "summary": "Apply PII.Sensitive tag to 12 columns across 5 tables",
    "expires_at": "2026-04-26T14:35:00.000+05:30"
  },
  "ts": "..."
}
```

### `POST /api/v1/chat/confirm`

Accept or reject a pending write proposal.

```json
{ "session_id": "uuid", "proposal_id": "uuid", "accepted": true }
```

### `POST /api/v1/chat/cancel`

Clear the current chat session.

```json
{ "session_id": "uuid" }
```

### `GET /api/v1/healthz`

Liveness + readiness. Functional from Phase 1.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "ts": "2026-04-19T...",
  "checks": { "app": { "ok": true } }
}
```

### `GET /api/v1/metrics`

Prometheus text format. Functional from Phase 1.

Series exposed:

- `agent_requests_total{endpoint, status_code}` — counter
- `agent_errors_total{code}` — counter
- `agent_request_latency_seconds{endpoint}` — histogram
- `agent_llm_tokens_used_total{direction, model}` — counter
- `agent_llm_calls_total{model, outcome}` — counter
- `agent_mcp_calls_total{tool_name, outcome}` — counter
- `agent_circuit_breaker_state{circuit}` — gauge (0=closed, 1=open, 2=half-open)
- `agent_pending_confirmations` — gauge
- `agent_active_sessions` — gauge

## Error envelope (every non-2xx)

```json
{
  "code": "om_unavailable",
  "message": "OpenMetadata is temporarily unreachable.",
  "request_id": "uuid",
  "ts": "ISO 8601 with timezone",
  "details": null
}
```

Standard codes: `validation_failed` (422), `tool_not_allowlisted` (422), `confirmation_required` (200), `confirmation_expired` (410), `proposal_not_found` (422), `om_unavailable` (503), `om_auth_failed` (502), `llm_unavailable` (503), `llm_invalid_output` (502), `llm_token_budget_exceeded` (429), `github_unavailable` (503), `rate_limited` (429), `not_implemented` (501), `internal_error` (500).

The `message` field is always a canonical safe string — never includes API keys, JWTs, file paths, full prompts, or raw exceptions (per [`SECURITY.md`](../SECURITY.md) SC-8).
