# Non-Functional Requirements

> Phase 2 deliverable per [Feature-Dev SKILL.md §The 5 Things AI Never Adds](../../agents/Feature-Dev/SKILL.md).
>
> **Critical**: if these aren't in this doc, they will NOT be in the code. Reviewers MUST cite a specific NFR-N row when approving any PR that touches an external call.

## NFR-01 Performance

| Metric                                               | Target                | Measurement                             |
| ---------------------------------------------------- | --------------------- | --------------------------------------- |
| `POST /chat` p95 latency (single-tool query)         | < 3.0s                | structlog timing field on every request |
| `POST /chat` p95 latency (multi-step, 3+ tool calls) | < 8.0s                | same                                    |
| Auto-classification of 50 tables                     | < 60s wall-clock      | Demo timer                              |
| LLM call (per turn)                                  | < 8.0s with 1 retry   | OpenAI `request_timeout=8.0`            |
| Single OM MCP tool call                              | < 5.0s with 3 retries | `data-ai-sdk` config                    |

## NFR-02 Scalability

| Aspect                          | v1 Target                    | 12-month (out of scope, documented only)                       |
| ------------------------------- | ---------------------------- | -------------------------------------------------------------- |
| Concurrent chat sessions        | 1 (demo)                     | 10                                                             |
| OM entities scanned per session | 100 (demo: 50)               | 10,000 (would require pagination + result streaming)           |
| Tokens per LLM call             | < 4,000 input + 1,000 output | same — token budget is a security control, not just a perf one |

## NFR-03 Availability

- v1: best-effort, single-process, single-host
- Demo window (5 min): zero unhandled exceptions; FastAPI returns a structured-error 5xx response on any backend failure rather than crashing the process

## NFR-04 Security

See [Security/ThreatModel.md](../Security/ThreatModel.md), [Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md), [Security/ControlCoverage.md](../Security/ControlCoverage.md), [Security/SecretsHandling.md](../Security/SecretsHandling.md). Headlines:

- All secrets via env (`AI_SDK_TOKEN`, `OPENAI_API_KEY`, `GITHUB_TOKEN`); never logged; never committed (`.env` in `.gitignore`)
- All LLM-suggested write tool calls (`patch_entity`, `create_glossary*`, `create_lineage`, GitHub `create_issue`) gated behind explicit user confirmation in the UI before execution
- All catalog content fetched from OM MCP and inserted into LLM prompts must be HTML/markdown-escaped and truncated to ≤ 500 chars per field (Module G mitigation)

## NFR-05 Data

- **Persistence**: in-memory only for v1 (chat session lives in the FastAPI process). Restart loses history. No database.
- **Logs**: rotate at 10 MB, keep 5 files, structured JSON; PII redaction filter active (see [Security/SecretsHandling.md](../Security/SecretsHandling.md))
- **Demo seed data**: checked into the repo as `seed/customer_db.json` so the demo is reproducible without an internet connection

## NFR-06 Observability

| Signal                  | Tool                                                                                         | Surface                                   |
| ----------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Structured logs         | `structlog` (JSON formatter)                                                                 | stdout + rotating file `logs/agent.log`   |
| Request correlation IDs | `request_id` UUID per `/chat` POST, propagated through every tool call and log line          | every log line, every error response      |
| 4 Golden Signals        | counters: requests_total, errors_total; histograms: request_latency_seconds, llm_tokens_used | `GET /metrics` (Prometheus text format)   |
| Trace                   | optional in v1 — note in roadmap                                                             | OpenTelemetry compatible structlog output |

See [Architecture/Overview.md §Observability](../Architecture/Overview.md) and ADR-08 in [Decisions.md](./Decisions.md).

## NFR-07 Deployability

- One-command bring-up: `make demo` (or `docker compose up`) starts OM (existing) + agent backend + UI
- Rollback: `git checkout v0.1.0 && docker compose down && docker compose up` — < 2 min
- No production deployment for v1 (out of scope)

## NFR-08 Compliance

None claimed. Apache 2.0 OSS submission.

---

## The 5 Things AI Never Adds — Concrete Implementation Contract

> Per [Feature-Dev SKILL.md line 227-237](../../agents/Feature-Dev/SKILL.md). Each row is a hard contract that PR review MUST verify.

### 1. Retry logic

| External call                        | Retries | Backoff                             | Conditions                                                             |
| ------------------------------------ | ------- | ----------------------------------- | ---------------------------------------------------------------------- |
| OM MCP tool call (via `data-ai-sdk`) | 3       | exponential, base 0.5s, jitter ±20% | retry on 429, 500, 502, 503, 504                                       |
| OpenAI chat completion               | 2       | exponential, base 1.0s              | retry on `RateLimitError`, `APIConnectionError`, `InternalServerError` |
| GitHub MCP `create_issue`            | 2       | exponential, base 0.5s              | retry on 429, 5xx                                                      |
| Anything else                        | 0       | —                                   | fail fast and report                                                   |

### 2. Circuit breakers

| Circuit    | Failure threshold                 | Cooldown | Behavior when open                                                                                                                    |
| ---------- | --------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| OM MCP     | 5 consecutive failures within 30s | 30s      | return `{"code":"om_unavailable","message":"OpenMetadata is temporarily unreachable","request_id":...}` to chat UI without calling OM |
| OpenAI     | 5 consecutive failures within 60s | 60s      | return `{"code":"llm_unavailable","message":"AI is temporarily unreachable; try again in a minute","request_id":...}`                 |
| GitHub MCP | 3 consecutive failures within 30s | 60s      | demote write to a logged note; return partial-success message to user                                                                 |

Use `pybreaker` or hand-rolled state machine; no `circuitbreaker` package (unmaintained).

### 3. Timeouts

| Call                          | Connect timeout | Read timeout                              |
| ----------------------------- | --------------- | ----------------------------------------- |
| OM MCP via `data-ai-sdk`      | 3.0s            | 5.0s                                      |
| OpenAI                        | 3.0s            | 8.0s                                      |
| GitHub MCP                    | 3.0s            | 5.0s                                      |
| FastAPI request handler total | —               | 30.0s (Uvicorn `--timeout-keep-alive 30`) |

### 4. Rate limiting

| Endpoint             | Limit        | Scope                                                           |
| -------------------- | ------------ | --------------------------------------------------------------- |
| `POST /chat`         | 30 req/min   | per client IP                                                   |
| `POST /chat/confirm` | 10 req/min   | per client IP                                                   |
| All other endpoints  | 60 req/min   | per client IP                                                   |
| OpenAI calls         | 20 calls/min | global (token bucket; protects from runaway agent loops + cost) |

Use `slowapi` (FastAPI middleware on top of `limits`).

### 5. Structured errors

Every error response from `POST /chat`, `POST /chat/confirm`, every backend exception, every log entry uses this envelope:

```json
{
  "code": "string — machine-readable, snake_case (e.g., 'om_unavailable', 'llm_invalid_output', 'tool_call_rejected')",
  "message": "string — human-readable, safe to render in UI; NEVER includes secrets, file paths, or stack traces",
  "request_id": "uuid — propagated end-to-end",
  "ts": "ISO-8601 with timezone",
  "details": { "optional_safe_metadata_only": "..." }
}
```

Banned in error messages: API keys, JWTs, file system paths, raw exceptions, full prompts, raw tool args containing user content, full SQL/queries.

---

## Verification

| NFR                        | Verified by                                                                                                | Owner    |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- | -------- |
| NFR-01 perf targets        | `pytest tests/perf/ -v` (light load harness)                                                               | OMH-PSTL |
| NFR-04 security headlines  | [Security/ControlCoverage.md](../Security/ControlCoverage.md) checklist                                    | OMH-GSA  |
| NFR-06 observability       | manual check that `/metrics` exposes 4 Golden Signals + every log has `request_id`                         | OMH-PSTL |
| The 5 Things AI Never Adds | [Validation/QualityGates.md §Resilience Review](../Validation/QualityGates.md) gate before each phase exit | OMH-GSA  |
