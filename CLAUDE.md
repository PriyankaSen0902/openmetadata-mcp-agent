# CLAUDE.md

> The architectural contract for AI agents (Claude / Cursor / Copilot) and human contributors working on this repo. Read this before writing any code.

## Project: openmetadata-mcp-agent

A standalone Python conversational governance agent for OpenMetadata. Built on the official `data-ai-sdk` + LangGraph + OpenAI. Submitted to the WeMakeDevs × OpenMetadata "Back to the Metadata" hackathon (Apr 17–26, 2026), Track T-01: MCP Ecosystem & AI Agents. Targets issues [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) (Multi-MCP Orchestrator) and [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608) (Conversational Data Catalog Chat App).

## Architecture

Pattern: **Modular Monolith** (single FastAPI process, layered).
See [`docs/architecture.md`](docs/architecture.md) for the system context, [`.idea/Plan/Architecture/Overview.md`](.idea/Plan/Architecture/Overview.md) for internal detail.

```
src/copilot/
├── api/             ← HTTP layer ONLY. Routing, validation, response shaping.
├── services/        ← Business logic. NO HTTP. NO direct external calls.
├── clients/         ← External system clients (om_mcp, openai, github_mcp).
├── models/          ← Pydantic models. Single source of truth for shapes.
├── middleware/      ← request_id, rate-limit, error envelope, logging.
├── config/          ← Pydantic Settings, env loading.
└── observability/   ← structlog + prometheus + redaction processor.
```

**Layer rules** (enforced by `tests/architecture/test_layer_imports.py`):

- `api/` may call `services/`. Never `clients/`. Never `models/` directly to construct DB rows.
- `services/` may call `clients/` and `models/`. Never raises HTTP types or knows about request/response objects.
- `clients/` are the only place external HTTP/SDK calls happen.

## Tech stack

- Frontend: React 18 + Vite 5 + TypeScript 5 (strict, no `any`, no MUI) — in `ui/` (`npm ci` + `npm run dev` → `http://localhost:3000`; see `ui/README.md`)
- Backend: Python 3.11+ + FastAPI 0.110+ + Uvicorn 0.27+
- Agent: LangGraph + langchain-openai
- MCP Client: `data-ai-sdk[langchain]` (official OpenMetadata SDK)
- LLM: OpenAI GPT-4o-mini (free Codex Hackathon credits)
- Resilience: httpx + tenacity + pybreaker + slowapi
- Observability: structlog (JSON) + prometheus-client
- Testing: pytest + pytest-asyncio + respx + Playwright
- Lint/Type: ruff + mypy --strict
- CI: GitHub Actions

Pin every dependency to an exact version. No `~=` or `^` during the hackathon week. See `requirements.lock`.

## Code Conventions

### The Three Laws of Implementation (NON-NEGOTIABLE)

1. **Layer Separation is Sacred** — API → Service → Client. Never skip.
2. **Handle Every Error Path** — every external call has a documented failure mode and a structured error envelope response.
3. **Every External Call Has Defense** — timeout + retry + circuit breaker. No bare `requests.get(url)` or `openai.chat.completions.create(...)`.

### The 5 Things AI Never Adds (ENFORCED in code review)

Every PR touching an external call must satisfy:

- [ ] Retry: exponential backoff, jitter, max attempts per [`.idea/Plan/Project/NFRs.md`](.idea/Plan/Project/NFRs.md)
- [ ] Circuit breaker: `pybreaker` wrapping the client
- [ ] Timeout: connect + read, both set explicitly
- [ ] Rate limit: `slowapi` middleware on the route
- [ ] Structured error: response uses the envelope from [`.idea/Plan/Architecture/APIContract.md`](.idea/Plan/Architecture/APIContract.md)

### Naming

- snake_case Python; camelCase TS; SCREAMING_SNAKE for constants.
- Functions are verb-first: `classify_columns`, `apply_tags`.
- Modules are nouns: `classifier.py`, `lineage_summarizer.py`.
- Tests mirror module names: `tests/unit/test_classifier.py`.
- Booleans are question-form: `is_active`, `has_permission`, `can_retry`. NEVER `flag`, `status`, `check`.

### Errors

- Always raise typed exceptions (`McpUnavailable`, `LlmInvalidOutput`, `ToolNotAllowlisted`, etc.).
- Never raise bare `Exception` or `RuntimeError` from business logic.
- Catch at the API boundary; return the envelope per [APIContract.md](.idea/Plan/Architecture/APIContract.md).

### Tests

- Every new function in `services/` or `clients/` has a unit test.
- Mock external SDKs (`data-ai-sdk`, `openai`) — never call them in unit tests.
- `pytest tests/unit/` must run in <10s.

### Logging

- `structlog` only. NEVER `print()` or `logging.info()` directly.
- Every log line includes `request_id` (use `structlog.contextvars` to bind).
- NEVER log: API keys, JWTs, full prompts, full tool args containing user data. Use the redaction processor in `src/copilot/observability/redact.py`.

### Secrets

- Environment variables only. `.env.example` checked in. `.env` in `.gitignore`.
- Three secrets: `AI_SDK_TOKEN`, `OPENAI_API_KEY`, `GITHUB_TOKEN` (Phase 3 only).
- See [`.idea/Plan/Security/SecretsHandling.md`](.idea/Plan/Security/SecretsHandling.md).

### Git

- Branch names: `phase-N-feature-name` (e.g. `phase-2-auto-classify`).
- Commit messages: lowercase, present tense, what changed:
  - GOOD: `add patch_entity client with retry and circuit breaker`
  - BAD: `feat: implement comprehensive patch_entity integration with...`
- NEVER `git add .` — explicit filenames only.
- NEVER commit secrets, .env, debug files.

### PRs

- Use the template at `.github/PULL_REQUEST_TEMPLATE.md`.
- Reviewed by @GunaPalanivel against [`.idea/Plan/PR-Review/Checklist.md`](.idea/Plan/PR-Review/Checklist.md).
- Must pass CI (lint, types, tests, security scan) before review.

## Non-Negotiables

- [ ] Every external call has a timeout (Three Laws Law 3)
- [ ] Every write tool call goes through the HITL confirmation gate (Module G)
- [ ] LLM-fetched catalog content is escaped + truncated to ≤500 chars before reaching any LLM prompt (`src/copilot/services/prompt_safety.py`)
- [ ] LLM JSON output is Pydantic-validated before any tool execution
- [ ] FastAPI binds to `127.0.0.1` only (NEVER `0.0.0.0`) in v1
- [ ] No `pickle.load` or `joblib.load` anywhere — JSON only
- [ ] No `print()` in production code paths
- [ ] No `requests` — use `httpx` (timeout-default)

## Reading order for AI sessions

1. This file (you are here)
2. [`CodePatterns.md`](CodePatterns.md) — language/framework conventions
3. [`CONTRIBUTING.md`](CONTRIBUTING.md) — branch / PR / review workflow
4. [`docs/architecture.md`](docs/architecture.md) — system context
5. [`.idea/Plan/Project/Discovery.md`](.idea/Plan/Project/Discovery.md) — what we are building and why
6. [`.idea/Plan/Project/NFRs.md`](.idea/Plan/Project/NFRs.md) — concrete numbers (timeouts, retries, etc.)
7. [`.idea/Plan/Architecture/APIContract.md`](.idea/Plan/Architecture/APIContract.md) — every endpoint's shape
8. [`.idea/Plan/Architecture/DataModel.md`](.idea/Plan/Architecture/DataModel.md) — every Pydantic model
9. [`.idea/Plan/Security/ThreatModel.md`](.idea/Plan/Security/ThreatModel.md) — trust boundaries and SC-N claims

## Current Phase

**Phase 1 (Foundation)** — see [`.idea/Plan/TaskSync.md`](.idea/Plan/TaskSync.md) for the live task list.
