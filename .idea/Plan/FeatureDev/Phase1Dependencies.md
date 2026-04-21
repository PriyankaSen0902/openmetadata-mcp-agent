# Phase 1 Dependencies — `pyproject.toml` (P1-01 / #14)

## Owner: OMH-GSA (Guna)

## Phase: 1 (Foundation, Day 3–4)

## Tracks: [P1-01](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/14) → unblocks [#16](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/16) (MCP client)

---

## Overview

Five runtime dependencies are required for the agent to function end-to-end: one official
OpenMetadata Python SDK, one LLM orchestration library, one LLM binding, one ASGI
framework, and one ASGI server. This spec pins each, cross-references the rationale in
[Project/TechStackDR.md](../Project/TechStackDR.md), and records how the install +
`make ci-local` gates were validated before unblocking #16.

## The Five Phase 1 Deps

| # | Package | Pin (in `pyproject.toml`) | Resolved at verify | Role | Rationale (TechStackDR §) |
|---|---------|----------------------------|--------------------|------|----------------------------|
| 1 | `data-ai-sdk[langchain]` | `==0.1.2` | `0.1.2` | Official OM Python SDK — typed `MCPTool` enum, `client.mcp.as_langchain_tools()`, `AI_SDK_HOST` / `AI_SDK_TOKEN` wiring | [MCP Client](../Project/TechStackDR.md) |
| 2 | `langgraph` | `>=0.2.0,<0.3.0` | `0.2.76` | State-machine orchestration: `intent → tool select → execute → validate → confirm → respond` | [Agent Orchestration](../Project/TechStackDR.md) |
| 3 | `langchain-openai` | `>=0.2.0,<0.3.0` | `0.2.14` | LangChain binding for OpenAI GPT-4o-mini; paired with `langgraph` tool-calling | [LLM Provider](../Project/TechStackDR.md) |
| 4 | `fastapi` | `>=0.110.0,<0.120.0` | `0.119.1` | ASGI framework for `/api/v1/chat`, `/api/v1/healthz`, `/api/v1/metrics`; free OpenAPI docs | [Backend](../Project/TechStackDR.md) |
| 5 | `uvicorn[standard]` | `>=0.27.0,<0.40.0` | `0.39.0` | Async server for FastAPI; `[standard]` pulls `uvloop` + `httptools` for perf | [Backend](../Project/TechStackDR.md) |

> `langchain-mcp-adapters` is intentionally **not** in Phase 1. `data-ai-sdk[langchain]` already
> exposes `client.mcp.as_langchain_tools()` for OM, so the adapter is only needed in Phase 3
> when wiring the GitHub MCP server — per [TaskSync.md](../TaskSync.md) note at P1-01.

## Verification Commands

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

python -c "
import importlib, importlib.metadata as md
for mod, dist in [('fastapi','fastapi'),('uvicorn','uvicorn'),
                  ('langgraph','langgraph'),('langchain_openai','langchain-openai'),
                  ('ai_sdk','data-ai-sdk')]:
    importlib.import_module(mod)
    print(f'{mod:20s} {md.version(dist)}')
"

make ci-local
```

## Done when

- [x] All five deps listed in [`pyproject.toml`](../../../pyproject.toml) lines 40–53
- [x] `pip install -e ".[dev]"` exits 0 on Python 3.11.15 (log attached in PR)
- [x] Five deps import cleanly and resolve to the versions in the table above
- [ ] `make ci-local` is green end-to-end — see "Known pre-existing failures" below; the
      pre-commit and license-header gates fail for reasons unrelated to the five Phase-1
      deps. Fixes are tracked as separate follow-up issues per the P1-01 scope rule.

## Known pre-existing failures (out of scope for P1-01)

These are reported, not fixed, in this task. They will be addressed in follow-up issues so
P1-01 can close cleanly and #16 can proceed.

1. **`tests/conftest.py` has CRLF line endings.** `ruff` auto-rewrites them to LF when the
   `pre-commit-all` hook runs, which fails the `files were modified by this hook` gate.
   Root cause: file was checked in with Windows line endings. Fix: one-line re-save with
   LF + commit. Does not involve the five Phase-1 deps.
2. **`scripts/check_license_headers.py` scans `.git/`.** The `SKIP_PATH_PARTS` set (line 22
   of that script) omits `.git`, so local user scripts that happen to live inside the
   `.git/` metadata directory get flagged as missing an Apache 2.0 header. Fix: add `.git`
   to `SKIP_PATH_PARTS`. Again unrelated to Phase-1 deps.

Both failures reproduce on `main` (branch `phase-1/p1-01-pin-deps` has zero commits over
`main` at the time of P1-01 validation), which confirms they are pre-existing.

## Exit criteria

- PR closes #14
- Progress.md row for P1-01 is marked through `PR opened` (the reviewer ticks `R` and `M`)
- Follow-up issues are open for the two `make ci-local` gate failures above so #16 is
  truly unblocked and not just deferred
