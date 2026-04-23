# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), version numbers follow [SemVer](https://semver.org/).

## [Unreleased]

### Verified

- **P1-14 / [#27](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/27)** — Vite dev server on `:3000` (`ui/vite.config.ts`); committed `ui/package-lock.json`; CI `ui-build` and `make install_ui` use `npm ci`; `ui/public/favicon.svg`; `ui/README.md` runbook; `@types/react-dom` aligned with React 18. PR: [#73](https://github.com/GunaPalanivel/openmetadata-mcp-agent/pull/73).

### Added

- **P1-12 / [#25](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/25)** — `scripts/generate_bot_jwt.py` and `make om-gen-token` target to automate Bot JWT generation from a running OM instance. Connects to OM REST API, authenticates as admin, looks up `ingestion-bot`, and generates a configurable-expiry JWT printed to stdout for `.env` pasting. Docs updated in `docs/getting-started.md` (Step 3).

### Verified

- **P1-01 / [#14](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/14)** — Phase 1 runtime dependencies install clean on Python 3.11.15: `data-ai-sdk[langchain]==0.1.2`, `langgraph==0.2.76`, `langchain-openai==0.2.14`, `fastapi==0.119.1`, `uvicorn[standard]==0.39.0`. All five imports resolve via `pip install -e ".[dev]"`. Feature-Dev spec: [`.idea/Plan/FeatureDev/Phase1Dependencies.md`](.idea/Plan/FeatureDev/Phase1Dependencies.md). Unblocks [#16](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/16).
- **P1-02 / [#15](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/15)** — Repo skeleton verified against layered architecture. All directories exist. Drift from flat to layered layout documented in [`.idea/Plan/FeatureDev/Phase1RepoSkeleton.md`](.idea/Plan/FeatureDev/Phase1RepoSkeleton.md). Layer boundaries enforced by [`tests/architecture/test_layer_imports.py`](tests/architecture/test_layer_imports.py).

## [0.1.0] - 2026-04-19

### Added

- Initial scaffold for `openmetadata-mcp-agent` (BUILD Phase 1 of [`.idea/Plan/TaskSync.md`](.idea/Plan/TaskSync.md))
- Repository structure mirroring OpenMetadata's layered conventions (api / services / clients / models / middleware / config / observability)
- FastAPI app factory with `/api/v1/healthz` (functional), `/api/v1/metrics` (Prometheus), `/api/v1/chat` (stub returning structured `not_implemented` envelope)
- Full Pydantic v2 models: `ChatSession`, `ToolCallProposal`, `ToolCallRecord`, `ClassificationJob`, `TagSuggestion`, `LineageImpactReport`, `LineageNode`, `ErrorEnvelope`
- `services/prompt_safety.neutralize()` — Module G Layer-1 input neutralization (escape + truncate + instruction-pattern flagging) covering 5 canonical injection patterns
- `middleware/request_id.py` — UUID propagation through `structlog.contextvars`
- `middleware/error_envelope.py` — typed exception → structured error envelope (`code`, `message`, `request_id`, `ts`)
- `middleware/rate_limit.py` — slowapi gates per [`.idea/Plan/Project/NFRs.md`](.idea/Plan/Project/NFRs.md)
- `config/settings.py` — Pydantic Settings with `SecretStr` for the 3 secrets, `host=127.0.0.1` (SC-1), all NFR resilience knobs
- `observability/redact.py` — structlog processor that strips known secret values from log lines
- `observability/metrics.py` — Prometheus counters/histograms for the 4 Golden Signals + token usage + circuit-breaker state
- `tests/unit/test_smoke.py` — imports every module + asserts `/healthz` returns 200
- `tests/security/test_prompt_injection.py` — 5 canonical patterns from [`.idea/Plan/Security/PromptInjectionMitigation.md`](.idea/Plan/Security/PromptInjectionMitigation.md)
- `tests/architecture/test_layer_imports.py` — enforces Three Laws of Implementation Law 1 (layer separation)
- `ui/` — Vite + React 18 + TypeScript 5 chat shell with OM brand styling (`#7147E8`, Inter, dark mode)
- `seed/` — frozen demo dataset placeholder (will hold 50+ tables in Phase 2)
- `scripts/` — `load_seed.py`, `smoke_test.py`, `check_openai_quota.py`
- `infrastructure/docker-compose.yml` — agent backend service (OM is assumed running externally)
- `docs/` — public documentation (getting-started, architecture, api, runbook, contributing)
- `.github/workflows/ci.yml` — full hardened pipeline: lint + typecheck + unit tests + security scan + secret scan + UI build + path-guard (per [`.idea/Plan/Security/CIHardening.md`](.idea/Plan/Security/CIHardening.md))
- `.github/dependabot.yml` — pip + actions + npm weekly
- `.github/PULL_REQUEST_TEMPLATE.md` — adapted from [`.idea/Plan/PR-Review/PRTemplate.md`](.idea/Plan/PR-Review/PRTemplate.md) with all four review gates (Architecture / Resilience / Observability / AI-ML Security)
- `.github/ISSUE_TEMPLATE/` — task / feature / bug templates referencing TaskSync IDs
- `CLAUDE.md` — top-level architecture contract for AI agents
- `CodePatterns.md` — code conventions mirroring OpenMetadata (Python pytest/Pydantic, TypeScript no-`any`/no-`console.log`, comments policy, git, license headers)
- `LICENSE_HEADER.txt` — Apache 2.0 source-file header
- Pre-commit hooks: ruff + gitleaks (SHA-pinned)
- `.gitignore` — curated to publish ~38 of 48 internal planning docs (strong engineering-process signal) while keeping 8 tactical/sensitive files private

### Defense-in-depth highlights

- **Five trust zones** documented (browser → agent backend → LLM provider → OpenMetadata MCP → GitHub MCP)
- **Three independent gates** between LLM output and any write: Pydantic schema validation → tool allowlist → HITL confirmation
- **No `pickle` / `joblib` / `eval` / `exec` / `os.system`** anywhere — bandit + ruff enforce
- **Secret redaction** in every log line (defense against accidental f-string interpolation)
- **Circuit breakers** on every external call (OM MCP, OpenAI, GitHub MCP)

### Hackathon

Submitted to WeMakeDevs × OpenMetadata "Back to the Metadata" hackathon (Apr 17–26, 2026), Track T-01: MCP Ecosystem & AI Agents. Targets issues [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) and [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608). Team: The Mavericks (Guna Palanivel, Priyanka Sen, Aravind Sai, Bhawika Kumari).
