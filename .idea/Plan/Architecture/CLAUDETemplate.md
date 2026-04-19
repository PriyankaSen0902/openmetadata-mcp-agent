# `CLAUDE.md` Template for the New Repo

> Phase 5 deliverable per [Feature-Dev SKILL.md](../../agents/Feature-Dev/SKILL.md). Drop this verbatim into the root of `openmetadata-mcp-agent/` once the repo is created. Future AI sessions inherit the architectural contract from this file. Update the "Current Phase" line as the team progresses.

---

```markdown
# CLAUDE.md

## Project: OpenMetadata MCP Agent

A standalone Python conversational governance agent for OpenMetadata. Built on
the official `data-ai-sdk` + LangGraph + OpenAI. Submitted to the WeMakeDevs ×
OpenMetadata "Back to the Metadata" hackathon (Apr 17-26, 2026), Track T-01:
MCP Ecosystem & AI Agents. Targets issues #26645 (Multi-MCP Orchestrator) and
#26608 (Conversational Data Catalog Chat App).

## Architecture

Pattern: Modular Monolith (single FastAPI process, layered).
See: docs/architecture.md.
```

src/copilot/
├── api/ ← HTTP layer ONLY. Routing, validation, response shaping.
├── services/ ← Business logic. NO HTTP. NO direct external calls.
├── clients/ ← External system clients (om_mcp, openai, github_mcp).
├── models/ ← Pydantic models. Single source of truth for shapes.
├── middleware/ ← request_id, rate-limit, logging, error envelope.
├── config/ ← Pydantic Settings, env loading.
└── observability/ ← structlog, prometheus.

```

Layer rules (enforced by code review per `docs/architecture.md` and
`.idea/Plan/Architecture/CodingStandards.md`):
- API may call services. Never clients. Never models directly to construct DB rows.
- Services may call clients and models. Never HTTP request objects.
- Clients are the only place external HTTP/SDK calls happen.

## Tech Stack
- Frontend: React 18 + Vite 5 + TypeScript 5 (in `ui/`)
- Backend: Python 3.11+ + FastAPI 0.110+ + Uvicorn 0.27+
- Agent: LangGraph + langchain-openai
- MCP Client: `data-ai-sdk[langchain]` (official OM SDK)
- LLM: OpenAI GPT-4o-mini (free Codex Hackathon credits)
- Observability: structlog (JSON) + prometheus-client
- Testing: pytest + pytest-asyncio + respx
- Lint/Type: ruff + mypy --strict
- CI: GitHub Actions

Pin every dependency to an exact version. No `~=` or `^` during the hackathon
week. See `requirements.lock`.

## Code Conventions

### The Three Laws of Implementation (NON-NEGOTIABLE)
1. **Layer Separation is Sacred** — API → Service → Client. Never skip.
2. **Handle Every Error Path** — every external call has a documented failure
   mode and a structured error envelope response.
3. **Every External Call Has Defense** — timeout + retry + circuit breaker.
   No bare `requests.get(url)` or `openai.chat.completions.create(...)`.

### The 5 Things AI Never Adds (ENFORCED)
Every PR touching an external call must satisfy:
- [ ] Retry: exponential backoff, jitter, max attempts per
      `.idea/Plan/Project/NFRs.md`
- [ ] Circuit breaker: `pybreaker` wrapping the client
- [ ] Timeout: connect + read, both set explicitly
- [ ] Rate limit: `slowapi` middleware on the route
- [ ] Structured error: response uses the envelope from
      `.idea/Plan/Architecture/APIContract.md`

### Naming
- Snake_case Python; camelCase TS; SCREAMING_SNAKE for constants
- Functions verb-first: `classify_columns`, `apply_tags`
- Modules noun: `classifier.py`, `lineage_summarizer.py`
- Tests mirror module names: `tests/unit/test_classifier.py`

### Errors
- Always raise typed exceptions (`McpUnavailable`, `LlmInvalidOutput`, ...)
- Never raise bare `Exception` or `RuntimeError` from business logic
- Catch at the API boundary; return the envelope per APIContract.md

### Tests
- Every new function in `services/` or `clients/` has a unit test
- Mock external SDKs (`data-ai-sdk`, `openai`) — never call them in unit tests
- `pytest tests/unit/` must run in <10s

### Logging
- `structlog` only. NEVER `print()` or `logging.info()` directly.
- Every log line includes `request_id`. Use `structlog.contextvars` to bind.
- NEVER log: API keys, JWTs, full prompts, full tool args containing user data.
  Use the redaction processor in `src/copilot/observability/redact.py`.

### Secrets
- Environment variables only. `.env.example` checked in. `.env` in `.gitignore`.
- Three secrets: `AI_SDK_TOKEN`, `OPENAI_API_KEY`, `GITHUB_TOKEN` (Phase 3 only).
- See `.idea/Plan/Security/SecretsHandling.md`.

### Git
- Branch names: `phase-N-feature-name` (`phase-2-auto-classify`)
- Commit messages: lowercase, present tense, what changed:
  `add patch_entity client with retry and circuit breaker`
  NOT: `feat: implement comprehensive patch_entity integration with...`
- NEVER `git add .` — explicit filenames only
- NEVER commit secrets, .env, debug files

### PRs
- Use the template at `.idea/Plan/PR-Review/PRTemplate.md`
- Reviewed by @GunaPalanivel against `.idea/Plan/PR-Review/Checklist.md`
- Must pass CI (lint, types, tests, security scan) before review

## Non-Negotiables
- [ ] Every external call has a timeout (Three Laws Law 3)
- [ ] Every write tool call goes through the HITL confirmation gate (Module G)
- [ ] LLM-fetched catalog content is escaped + truncated to ≤500 chars before
      reaching any LLM prompt (`src/copilot/services/prompt_safety.py`)
- [ ] LLM JSON output is Pydantic-validated before any tool execution
- [ ] FastAPI binds to `127.0.0.1` only (NEVER `0.0.0.0`) in v1
- [ ] No `pickle.load` or `joblib.load` anywhere — JSON only
- [ ] No `print()` in production code paths
- [ ] No `requests` — use `httpx` (timeout-default)

## Reading Order for AI Sessions
1. This file (you are here)
2. `.idea/Plan/Project/Discovery.md` — what we are building and why
3. `.idea/Plan/Project/NFRs.md` — concrete numbers (timeouts, retries, etc.)
4. `.idea/Plan/Architecture/Overview.md` — system context
5. `.idea/Plan/Architecture/APIContract.md` — every endpoint's shape
6. `.idea/Plan/Architecture/DataModel.md` — every Pydantic model
7. `.idea/Plan/Security/ThreatModel.md` — trust boundaries and SC-N claims
8. `.idea/Plan/PR-Review/Checklist.md` — what every PR must satisfy

## Current Phase
Phase 1 (Foundation) — see `.idea/Plan/TaskSync.md` for the live task list.
```

---

## How to use this template

1. After OMH-GSA creates the `openmetadata-mcp-agent` repo (P0-03), copy the
   markdown block above (between the triple-dash separators) verbatim into
   `openmetadata-mcp-agent/CLAUDE.md`.
2. Open the new repo in Cursor/VS Code; future AI sessions will read CLAUDE.md
   automatically.
3. At each Phase Exit Gate, update the "Current Phase" line.
4. NEVER drift CLAUDE.md from this template without also updating
   `.idea/Plan/Architecture/CLAUDETemplate.md`. They are paired.

## Why this matters for judging

Per [JudgePersona.md](../Project/JudgePersona.md): both Suresh and Sriharsha
will look at the new repo's root for evidence of engineering discipline.
A first-class `CLAUDE.md` that any teammate (or AI) can pick up and continue
from is a strong signal. Empty or boilerplate `CLAUDE.md` is a tell.
