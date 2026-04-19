# Coding Standards

> Phase 6 deliverable per [Feature-Dev SKILL.md §The Three Laws of Implementation](../../agents/Feature-Dev/SKILL.md). Python idioms for the `openmetadata-mcp-agent` repo. Every PR is reviewed against this doc.

## The Three Laws of Implementation

### Law 1: Layer Separation is Sacred

```
src/copilot/api/         ← HTTP layer ONLY: routing, request parsing, response shaping
                            NO business logic. NO direct external SDK calls.
src/copilot/services/    ← Business logic ONLY: orchestration, classification, decisions
                            NO HTTP types. NO direct SDK calls. Calls clients.
src/copilot/clients/     ← External system access ONLY: data-ai-sdk, openai, github_mcp
                            NO business rules. Returns domain types from models/.
src/copilot/models/      ← Pydantic models. Single source of truth for shapes.
src/copilot/middleware/  ← Cross-cutting: request_id, rate-limit, error envelope, logging
```

Cross-layer violations to reject in PR review:

| Violation                        | Example                                                         | Why bad                                         |
| -------------------------------- | --------------------------------------------------------------- | ----------------------------------------------- |
| API directly calling client      | `from copilot.clients.om_mcp import call_tool` in `api/chat.py` | Bypasses business logic; couples HTTP to SDK    |
| Service raising HTTPException    | `raise HTTPException(404, ...)` in `services/classifier.py`     | Pollutes business layer with HTTP concepts      |
| Client containing business logic | "if confidence > 0.7" in `clients/openai_client.py`             | Belongs in `services/classifier.py`             |
| Model with side effects          | `def save(self): db.write(...)` on a Pydantic model             | Models are dumb data; persistence is in clients |

**Enforced** by `tests/architecture/test_layer_imports.py` (uses `pydeps` or hand-rolled import scan; fails CI on cross-layer violations).

### Law 2: Handle Every Error Path

For every public function, the author must answer all of these BEFORE merge:

| Question                                    | If yes, what we do                                                                                                         |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| What if the input is invalid?               | Pydantic validation at the API boundary; raise `ValidationError`; return `validation_failed` envelope                      |
| What if the OM MCP server is down?          | Circuit breaker opens; raise `McpUnavailable`; return `om_unavailable` envelope (503)                                      |
| What if the LLM returns invalid JSON?       | Pydantic parse fails; raise `LlmInvalidOutput`; retry once; if still bad, return `llm_invalid_output` (502)                |
| What if this runs concurrently with itself? | Document expected behavior; for ChatSession, the LangGraph state graph is per-session-scoped (no shared mutable state)     |
| What if the user lacks permission?          | Bot JWT scopes the agent to whatever the bot user can do; OM returns 403 → return `om_auth_failed` (502)                   |
| What if the resource doesn't exist?         | Return `not_found` envelope; never crash                                                                                   |
| What if the call times out?                 | Configured timeout per [NFRs.md](../Project/NFRs.md) → retry per Law 3 → if still failing, return `*_unavailable` envelope |

The happy path is NOT done until all the above are answered explicitly. PR review rejects "I'll add error handling later".

### Law 3: Every External Call Has Defense

```python
# WRONG — no defense, will hang and crash on demo day
import requests
response = requests.get(url)

# WRONG — uses requests instead of httpx; no timeout; no retry
import requests
response = requests.get(url, timeout=5)
```

```python
# RIGHT — timeout + retry + circuit breaker
import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

om_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)

@om_breaker
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=4),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    reraise=True,
)
async def fetch_entity(fqn: str) -> dict:
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=3.0, read=5.0)) as client:
        response = await client.get(
            f"{settings.om_host}/api/v1/tables/name/{fqn}",
            headers={"Authorization": f"Bearer {settings.ai_sdk_token}"},
        )
        response.raise_for_status()
        return response.json()
```

For OpenAI: use the `openai` v1 SDK's built-in `timeout=` and `max_retries=`; wrap in `pybreaker`. For `data-ai-sdk`: configure `AI_SDK_TIMEOUT` and `AI_SDK_MAX_RETRIES` env vars; wrap in `pybreaker`.

## Per-Function Checklist

Author runs this before opening a PR. Reviewer verifies.

```
Before writing:
[ ] Does this belong in this layer? (api/services/clients/models)
[ ] What are ALL the error cases? (Law 2 questions answered)
[ ] How will I know this is working in production? (log line at entry/exit)

After writing:
[ ] Unit test written (happy path + 2 failure cases minimum)
[ ] structlog log at function entry with bound request_id
[ ] structlog log at function exit (success or failure)
[ ] Type hints on every parameter and return
[ ] Docstring (Google style: Args, Returns, Raises)
[ ] No secrets in code
[ ] No print()
[ ] No `requests` (use httpx)
[ ] Function is < 50 lines (refactor if longer)
```

## Python Standards

### Imports

- Standard library → third-party → first-party → relative; one group per block
- `from __future__ import annotations` at the top of every module that uses forward refs

### Type hints

- Required everywhere. No bare `dict`, `list`, `Any` without justification.
- `mypy --strict` gates CI. New violations fail.

### Pydantic

- v2 only. `BaseModel` with explicit field types and `Field(...)` for constraints.
- Mutation: use `.model_copy(update={...})`. NEVER mutate fields in place.

### Async

- FastAPI routes are `async def`.
- All clients are `async`.
- Never `await` inside a CPU-bound loop without yielding (use `asyncio.gather` for fan-out, not a `for` loop).

### Logging

```python
# WRONG
print(f"Classifying {table.fqn}")

# WRONG (no context, plain logging)
import logging
logger = logging.getLogger(__name__)
logger.info(f"Classifying {table.fqn}")

# RIGHT
import structlog
log = structlog.get_logger(__name__)
log.info("classification.start", fqn=table.fqn, columns=len(table.columns))
# ... operation ...
log.info("classification.complete", fqn=table.fqn, suggestions=len(suggestions))
```

### Error handling

```python
# WRONG
try:
    result = client.mcp.call_tool("patch_entity", args)
except Exception:
    pass  # silently swallow

# WRONG
try:
    result = client.mcp.call_tool("patch_entity", args)
except Exception as e:
    logger.error(str(e))  # leaks internal details to logs
    raise

# RIGHT
try:
    result = await om_client.call_tool("patch_entity", args)
except McpUnavailable as e:
    log.warning("om.circuit_open", request_id=request_id)
    raise
except McpAuthFailed as e:
    log.error("om.auth_failed", request_id=request_id)
    raise
except McpToolExecutionError as e:
    log.error("om.tool_failed", request_id=request_id, tool="patch_entity", error_code=e.error_code)
    raise
```

## TypeScript Standards (UI)

### Strict mode

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### React

- Function components with hooks. No class components.
- One component per file. File name = component name (`ChatMessage.tsx`).
- Props typed via `interface ChatMessageProps`. No anonymous types.
- No `any`. No `as` casts without a comment explaining why.

### State

- Local first (`useState`). Lift to `useReducer` if the same state has > 5 transitions.
- Server state via `@tanstack/react-query` (caches, retries, dedupes). NO global Redux for v1.

### Markdown rendering

- `react-markdown` + `rehype-sanitize`. NEVER `dangerouslySetInnerHTML`.

## Test Standards

### Coverage

- Target: 70% lines on `src/copilot/`, 100% on `models/` and `clients/` (smaller surface area, easier to fully cover)
- Reported via `pytest-cov --cov-fail-under=70` in CI

### Test naming

```python
# WRONG
def test_classifier(): ...
def test_classifier_2(): ...

# RIGHT
def test_classifier_returns_pii_tag_for_email_column(): ...
def test_classifier_returns_no_tag_when_confidence_below_threshold(): ...
def test_classifier_skips_obviously_non_personal_columns(): ...
```

### Mocks

```python
# RIGHT — respx for HTTP mocking
import respx

@respx.mock
async def test_om_client_retries_on_503():
    respx.get("http://localhost:8585/api/v1/tables/name/foo").mock(
        side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200, json={...})]
    )
    result = await om_client.fetch_entity("foo")
    assert result is not None
```

## What "done" means

A function is "done" when:

1. The Per-Function Checklist passes (all 8 items)
2. The PR includes a test that fails before the change and passes after
3. structlog confirms the function runs end-to-end with a `request_id` propagated
4. `ruff check`, `mypy --strict`, `pytest`, `pip-audit` all pass in CI
5. Reviewer (@GunaPalanivel) signs off against [PR-Review/Checklist.md](../PR-Review/Checklist.md)

Anything less is incomplete. Closing a TaskSync item without all five is the kind of corner-cutting Sriharsha would flag in a real code review (per [JudgePersona.md](../Project/JudgePersona.md)).
