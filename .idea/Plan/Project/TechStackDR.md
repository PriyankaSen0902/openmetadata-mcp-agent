# Tech Stack Decision Record

> Phase 3.3 deliverable per [Feature-Dev SKILL.md](../../agents/Feature-Dev/SKILL.md). Single consolidated table — no silent defaults. Every choice cites alternatives considered and rationale.

## Frontend

| Field                       | Value                                                                                                                                                                                                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Choice**                  | React 18 + Vite 5 + TypeScript 5                                                                                                                                                                                                                              |
| **Alternatives Considered** | Next.js (overkill for SPA), SvelteKit (smaller ecosystem for chat UIs), pure HTML+vanilla JS (no component reuse), Streamlit (judges score "User Experience" — Streamlit feels demo-y)                                                                        |
| **Rationale**               | Vite gives <100ms HMR for the 7-day build window; React has the largest set of chat-component primitives; TypeScript prevents the kind of demo-day bugs Sriharsha would spot ([JudgePersona.md](./JudgePersona.md))                                           |
| **Styling**                 | CSS variables matching OM brand (`#7147E8` primary — verified in [openmetadata-ui/src/main/resources/ui/src/styles/variables.less](../../../openmetadata-ui/src/main/resources/ui/src/styles/variables.less)); Inter font; dark mode default to match OM look |

## Backend

| Field                       | Value                                                                                                                                                                                                                                         |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Choice**                  | Python 3.11+ + FastAPI 0.110+ + Uvicorn 0.27+                                                                                                                                                                                                 |
| **Alternatives Considered** | Flask (no async, no Pydantic-native validation), Litestar (smaller community), Node.js + Express (would require porting `data-ai-sdk` JS — extra surface area), Go + chi (Python LLM ecosystem is richer)                                     |
| **Rationale**               | Python is required by `data-ai-sdk` (the official OM SDK); FastAPI gives free OpenAPI docs (judge can hit `/docs` live); async-native to avoid blocking on long LLM calls; Pydantic v2 for end-to-end validation including LLM output schemas |

## LLM Provider

| Field                       | Value                                                                                                                                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Choice**                  | OpenAI GPT-4o-mini (primary), GPT-4o (demo-only fallback for higher-quality narration)                                                                                                                                               |
| **Alternatives Considered** | Anthropic Claude (no free hackathon credits available to the team), Groq + Llama (the competitor on PR #27506 used this; less reliable function-calling), local Ollama (cold-start, demo risk), AWS Bedrock (account setup overhead) |
| **Rationale**               | Free OpenAI credits via Codex Hackathon Bengaluru promotion = zero cost blocker; best documented function-calling in LangChain/LangGraph; $0.15/1M input tokens enables hundreds of governance scans within demo budget              |
| **Env var**                 | `OPENAI_API_KEY` (in `.env`, never logged — see [Security/SecretsHandling.md](../Security/SecretsHandling.md))                                                                                                                       |

## Agent Orchestration

| Field                       | Value                                                                                                                                                                                                                                     |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Choice**                  | LangGraph (latest stable) + langchain-openai                                                                                                                                                                                              |
| **Alternatives Considered** | Raw OpenAI tool-calling loop (no state graph), AutoGen (heavy, less MCP-native), CrewAI (less control over tool routing), bare `data-ai-sdk` agent loop (no graph state)                                                                  |
| **Rationale**               | LangGraph state machine = explicit nodes for `intent → tool select → execute → validate → confirm → respond`, which gives a graph judges can read; native LangChain tool format means `client.mcp.as_langchain_tools()` plugs in directly |

## MCP Client

| Field                       | Value                                                                                                                                                                                                                                              |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Choice**                  | `data-ai-sdk[langchain]` v0.1.2+ (official OM Python SDK)                                                                                                                                                                                          |
| **Alternatives Considered** | Hand-rolled JSON-RPC client (reinvents the wheel; loses "uses official SDK" judging signal), `mcp` Python reference SDK (more generic, less OM-specific helpers), `langchain-mcp-adapters` for OM (works but `data-ai-sdk` is the OM-blessed path) |
| **Rationale**               | Best-Use-of-OpenMetadata judging criterion; auto-handles `AI_SDK_HOST` + `AI_SDK_TOKEN` env wiring; provides typed `MCPTool` enum for 7 tools (5 reachable by name); `as_langchain_tools()` ready for LangGraph                                    |
| **Phase 3 add**             | `langchain-mcp-adapters` ONLY for the GitHub MCP server (not OM); keeps OM path pure                                                                                                                                                               |

## Database / State

| Field                       | Value                                                                                                                                                              |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Choice**                  | None (in-memory only for v1)                                                                                                                                       |
| **Alternatives Considered** | SQLite (overkill for stateless chat), Redis (deployment complexity), `LangGraph SqliteSaver` (out-of-scope persistence)                                            |
| **Rationale**               | Per [NFRs.md §NFR-05](./NFRs.md), v1 is single-process; chat history is intentionally ephemeral; we document the path to Redis-backed sessions but do not build it |

## Auth

| Field                       | Value                                                                                                                                                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Choice (v1, dev only)**   | None on FastAPI ingress; the agent connects to OM MCP using a Bot JWT (`AI_SDK_TOKEN`); GitHub MCP uses a PAT (`GITHUB_TOKEN`)                                                                                                     |
| **Alternatives Considered** | OAuth via OM's own MCP OAuth flow (would require running the agent inside OM's auth domain — overkill for v1), API-key middleware on `/chat` (adds friction for the demo)                                                          |
| **Rationale**               | v1 runs on `localhost`; the Bot JWT scopes the agent to whatever the bot user can do in OM (good blast-radius limit); FastAPI bind to `127.0.0.1` only (NOT `0.0.0.0`) — see [Security/ThreatModel.md](../Security/ThreatModel.md) |
| **Roadmap**                 | v2 would add OM OAuth callback for per-user impersonation                                                                                                                                                                          |

## Observability

| Field         | Value                                                                                                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Logging**   | `structlog` 24+ with JSON formatter, stdout + rotating file at `logs/agent.log`; PII-redaction processor; `request_id` UUID propagated end-to-end                        |
| **Metrics**   | `prometheus-client` exposing `/metrics` with the 4 Golden Signals (counters: `requests_total`, `errors_total`; histograms: `request_latency_seconds`, `llm_tokens_used`) |
| **Tracing**   | Optional in v1 — structlog output is OpenTelemetry-compatible if a collector is added later                                                                              |
| **Alerting**  | Out of scope for v1 (no production deployment)                                                                                                                           |
| **Rationale** | Each row directly answers a likely judge question per [JudgePersona.md](./JudgePersona.md) Persona 2                                                                     |

## Infrastructure

| Field                       | Value                                                                                                   |
| --------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Choice**                  | Docker Compose (existing OM `docker/development/docker-compose.yml` + new agent service)                |
| **Alternatives Considered** | Kubernetes (overkill), bare-metal (demo machine fragility), cloud (account setup, demo network risk)    |
| **Rationale**               | One `make demo` command starts everything; reproducible across team laptops; matches OM's own dev setup |

## Testing

| Field                 | Value                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------- |
| **Unit**              | `pytest` + `pytest-asyncio` + `pytest-cov`; mocks for `data-ai-sdk` and OpenAI                     |
| **Integration**       | `pytest` with a real `data-ai-sdk` against a docker'd OM instance; `respx` for OpenAI HTTP mocking |
| **E2E**               | `playwright` for UI → backend → OM flow (Phase 3 only)                                             |
| **Linting**           | `ruff` (replaces black, isort, flake8)                                                             |
| **Type checking**     | `mypy --strict` on `src/copilot/`                                                                  |
| **Security scanning** | `pip-audit`, `bandit` (in CI per [Security/CIHardening.md](../Security/CIHardening.md))            |
| **Rationale**         | One canonical tool per concern; ruff/mypy gate the PRs Sriharsha would otherwise flag              |

## CI / CD

| Field                 | Value                                                                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Choice**            | GitHub Actions (workflows in `.github/workflows/ci.yml`)                                                                                             |
| **Permissions model** | `permissions: read-all` at workflow root; explicit job-level `contents: write` only where needed; SHA-pinned third-party actions; dependabot enabled |
| **Pipeline**          | lint → typecheck → unit tests → integration tests (only on push to main, against an OM container in services) → security scan                        |
| **Rationale**         | Demonstrates supply-chain hygiene per [Security/CIHardening.md](../Security/CIHardening.md); judges score "Technical Excellence"                     |

## Repository structure

```
openmetadata-mcp-agent/
├── .github/workflows/ci.yml           ← CI: lint, types, tests, audit
├── src/copilot/
│   ├── api/         ← FastAPI routes (HTTP layer ONLY)
│   ├── services/    ← business logic (agent orchestration, classification)
│   ├── clients/     ← external system clients (OM MCP, OpenAI, GitHub MCP)
│   ├── models/      ← Pydantic models (chat, jobs, audit log)
│   ├── middleware/  ← auth, rate limiting, logging, request_id
│   ├── config/      ← env loading, settings
│   └── observability/ ← structlog setup, metrics
├── tests/{unit,integration,e2e}/
├── ui/              ← React + Vite chat UI
├── seed/            ← frozen demo dataset (50+ tables) — see Demo/FailureRecovery.md
├── docs/{architecture,api,runbook}.md
├── infrastructure/docker-compose.yml
├── scripts/         ← seed loader, dev tools
├── .env.example     ← template (NEVER commit .env)
├── .gitignore
├── CLAUDE.md        ← see Architecture/CLAUDETemplate.md
├── Makefile         ← `make demo`, `make test`, `make lint`
└── README.md
```

## What we will NOT use (and why)

| Rejected                                       | Reason                                                                                                  |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `langchain-mcp-adapters` for the OM connection | `data-ai-sdk[langchain]` already provides `as_langchain_tools()`; adding another adapter is dead weight |
| `pickle` / `joblib` anywhere in the agent      | Unsafe deserialization is a Module-G concern; if we ever cache state, it's JSON only                    |
| `openai` v0.x SDK                              | We use the v1.x SDK (typed responses, retry-aware, async-first)                                         |
| Hand-rolled circuit breaker                    | `pybreaker` (PEP 8, maintained, < 200 LOC dependency); avoid `circuitbreaker` (unmaintained per PyPI)   |
| `requests` for any HTTP                        | `httpx` (async-aware, timeout-default) — Law 3 of Implementation says every external call has defense   |
