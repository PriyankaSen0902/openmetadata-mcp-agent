# TaskSync — Master Task Tracker

> **Last updated**: April 23, 2026 — aligned with repo + [Progress.md](./Progress.md); **Phase 2b** governance tasks; **§Sixteen-issue engineering program** + [EngineeringIssueTemplate.md](./PR-Review/EngineeringIssueTemplate.md). **Codebase snapshot — 2026-04-23** > **LLM Provider**: ✅ OpenAI GPT-4o-mini (free Codex credits)
> **Repo Strategy**: ✅ NEW standalone repo (`openmetadata-mcp-agent`) + fork for GFI only
> **Plan/ location**: ✅ `.idea/Plan/` stays local (agent command center)
> **All tasks ordered by priority. Check off as you complete them.**

**Quick pointers (code today):** Run the agent with `uvicorn copilot.api.main:app` (not root `main.py`). MCP: `src/copilot/clients/om_mcp.py` + env **`OM_MCP_HTTP_PATH`** (default `/mcp`). Seed: `scripts/load_seed.py` + `python-dotenv` + `dataLength` for OM 1.6; search index: `scripts/trigger_om_search_reindex.py`; `make demo-fresh` chains reindex after load. UI: [`ui/README.md`](../../ui/README.md) — **`npm ci`** / **`npm run dev`** on **`http://localhost:3000`** (Vite `127.0.0.1:3000`); committed **`ui/package-lock.json`**, **`ui/public/favicon.svg`**, CI **`ui-build`** uses **`npm ci`**; P1-14 / [#27](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/27) — PR [\#73](https://github.com/GunaPalanivel/openmetadata-mcp-agent/pull/73) (merge when green).

---

## Sixteen-issue engineering program (docs excluded)

> **Rule**: Exactly **16 closed GitHub issues** in `GunaPalanivel/openmetadata-mcp-agent` = engineering complete for the hackathon product bar. **README, submission form, narrative polish, and video script** are **not** in the 16 — they stay in Phase 3–4 tasks below.

| Wave   | Window       | Close (GitHub) | Exit                                                                                           |
| ------ | ------------ | ---------------- | ---------------------------------------------------------------------------------------------- |
| **W1** | Now → Apr 24 | [#75](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/75)–[#79](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/79) + start [#80](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/80) | HITL spine: P2-19…P2-24 per [FeatureDev/GovernanceEngine.md](./FeatureDev/GovernanceEngine.md) |
| **W2** | Apr 24–25    | [#80](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/80)–[#85](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/85) | Auto-classify, lineage, NL query, UI + HITL modal, OM-native UI                                |
| **W3** | Apr 25–26    | [#86](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/86)–[#90](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/90) | Multi-MCP, integration/security/coverage, CI gaps, demo automation, **E2E Playwright**         |

**Issue index**: [SPRINT16_GITHUB_ISSUES.md](./SPRINT16_GITHUB_ISSUES.md) · [SPRINT16_GITHUB_ISSUES.json](./SPRINT16_GITHUB_ISSUES.json) · Creator script: not committed in this repo; use the issue index files above as the canonical source.

**Issue bodies**: Mandatory template — [PR-Review/EngineeringIssueTemplate.md](./PR-Review/EngineeringIssueTemplate.md) (Context, What to do, Done when, Depends on, Unblocks, Acceptance criteria with PRD + APIContract + tests, References).

**Superseded**: GOV [#60](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/60)–[#66](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/66) and legacy Phase-1 open batch — closed with pointer to **#75–#90** (see this PR).

---

## Phase 0 — Claim & Setup (IMMEDIATE — Today April 19)

> ⚠️ **No formal assignment**: Per @PubChimps's Apr 18, 2026 comments on [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) and [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608): _"We will not be assigning this issue, this is just an idea of something that could be submitted for it!"_ Hackathon ideas are open competition — comment to **signal coordination**, not to claim. Build & submit regardless.

### OMH-GSA (@GunaPalanivel) — CRITICAL

- [x] `P0-01` 🔴 Post intent comment on [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) (Multi-MCP Orchestrator) and start building immediately — competing prototypes already exist (@0xSaksham LangGraph, @MonotonousHarsh, @afifasyed123)
- [x] `P0-02` 🔴 Post intent comment on [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608) (Chat App) and start building immediately — @thisisvaishnav already shared a [working Loom demo](https://www.loom.com/share/c2fc5f9fb9314c279faa1fc9967576f3) using Claude + MCP tool chaining
- [x] `P0-03` Create NEW repo: `GunaPalanivel/openmetadata-mcp-agent` on GitHub (public, Apache 2.0)
- [ ] `P0-04` Redeem OpenAI API credits at platform.openai.com/promotions _(per-person / optional for Codex path)_
- [ ] `P0-05` Generate OpenAI API key, save in `.env` _(blocked until P0-04 if using paid promo only)_
- [x] `P0-06` Add all team as collaborators: @PriyankaSen0902, @aravindsai003, @5009226-bhawikakumari
- [x] `P0-07` Drop the `CLAUDE.md` template from [Architecture/CLAUDETemplate.md](./Architecture/CLAUDETemplate.md) into the new repo root so all future AI sessions inherit the architectural contract
- [x] `P0-08` Star [open-metadata/OpenMetadata](https://github.com/open-metadata/OpenMetadata) — hackathon side-quest requirement (all 4 team members)
- [x] `P0-09` Read [Project/Discovery.md](./Project/Discovery.md), [Project/NFRs.md](./Project/NFRs.md), [Architecture/CodingStandards.md](./Architecture/CodingStandards.md), and [Security/PromptInjectionMitigation.md](./Security/PromptInjectionMitigation.md) — every team member, before writing any code (45 min total)
- [x] `P0-10` Every team member: after `make install_dev_env`, run `pip install pre-commit && pre-commit install && pre-commit run --all-files`. Same hooks as CI; commits that skip them will fail PR review. See [Validation/SetupGuide.md §Step 4b](./Validation/SetupGuide.md) and [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

### Intent Comment Template (for #26645 / #26608):

```
Hi @PubChimps — sharing what The Mavericks (team of 4) are building for this idea.

Team: @GunaPalanivel @PriyankaSen0902 @aravindsai003 @5009226-bhawikakumari

Approach:
- Standalone Python project using official `data-ai-sdk` + LangGraph + OpenAI GPT-4o-mini
- Connects OM MCP server (all 12 tools) + GitHub MCP server for cross-platform workflows
- Cross-MCP demo: "find PII tables → open a GitHub issue per table for the data steward"
- React chat UI with human-in-the-loop confirmation for write operations (patch_entity)
- Standalone repo: github.com/GunaPalanivel/openmetadata-mcp-agent (link to follow)

Posting here for coordination only — understood that this is open competition, not assigned.
We'll link the final submission + demo video before the Apr 26 deadline.
```

---

## Phase 1 — Foundation (Day 3–4: April 19–20)

### OMH-GSA (@GunaPalanivel) — Architect

- [x] `P1-01` Init `openmetadata-mcp-agent` repo with `pyproject.toml`
  - Deps (Phase 1): `data-ai-sdk[langchain]`, `langchain-openai`, `langgraph`, `fastapi`, `uvicorn`, `python-dotenv` (for seed/reindex scripts)
  - Note: `data-ai-sdk[langchain]` already provides `client.mcp.as_langchain_tools()`, so `langchain-mcp-adapters` is **not** needed for OM. Add it in Phase 3 only when wiring the GitHub MCP server.
- [x] `P1-02` Create basic project structure (see [FeatureDev/Phase1RepoSkeleton.md](./FeatureDev/Phase1RepoSkeleton.md) for planned-vs-actual, drift map, and verification):
  ```
  openmetadata-mcp-agent/
  ├── pyproject.toml
  ├── README.md
  ├── .env.example
  ├── .gitignore
  ├── src/copilot/                  ← layered per Architecture/Overview.md + CodePatterns.md
  │   ├── __init__.py
  │   ├── api/                      ← FastAPI routes (thin orchestrators)
  │   ├── services/                 ← business logic (agent, governance, prompt_safety)
  │   ├── clients/                  ← external I/O (om_mcp = data-ai-sdk wrapper, openai_client)
  │   ├── models/                   ← Pydantic v2 models
  │   ├── middleware/               ← request_id / error_envelope / rate_limit
  │   ├── config/                   ← Pydantic Settings (SecretStr, NFR knobs)
  │   └── observability/            ← structlog + Prometheus + PII redaction
  ├── ui/                           ← React chat (Phase 2)
  ├── tests/                        ← unit / security / architecture (layer-boundary)
  ├── scripts/
  ├── infrastructure/
  ├── docs/
  └── seed/
  ```
- [x] `P1-03` Implement MCP client: [`src/copilot/clients/om_mcp.py`](../../src/copilot/clients/om_mcp.py) (not `mcp_client.py` — wraps `data-ai-sdk`, `call_tool`, typed helpers; **`OM_MCP_HTTP_PATH`** for non-default MCP route)
- [x] `P1-04` Build LangGraph agent skeleton: [`src/copilot/services/agent.py`](../../src/copilot/services/agent.py) — NL → intent → tools → format
- [x] `P1-05` Verify: use `python scripts/smoke_test.py` (with `--include-om` when OM + agent are up); MCP success still depends on OM URL/token/index
- [ ] `P1-06` Review all Phase 1 PRs from team

### OMH-PSTL (@PriyankaSen0902) — Senior Builder

- [x] `P1-07` Study `data-ai-sdk` + `langchain-openai` docs — document tool schemas (see [DataFindings/ExistingMCPAudit.md](./DataFindings/ExistingMCPAudit.md))
- [x] `P1-08` Map all 12 MCP tools to governance use-cases → update `ExistingMCPAudit.md`. Split: **7 typed enum tools** (`SEARCH_METADATA`, `GET_ENTITY_DETAILS`, `GET_ENTITY_LINEAGE`, `CREATE_GLOSSARY`, `CREATE_GLOSSARY_TERM`, `CREATE_LINEAGE`, `PATCH_ENTITY`) reachable via `MCPTool.X`; **5 string-callable tools** (`semantic_search`, `get_test_definitions`, `create_test_case`, `create_metric`, `root_cause_analysis`) reachable via `client.mcp.call_tool("name", args)`
- [x] `P1-09` Create typed wrapper for top 6 tools — [`src/copilot/models/mcp_tools.py`](../../src/copilot/models/mcp_tools.py)
- [x] `P1-10` Write 10+ unit tests for MCP client wrapper — [`tests/unit/test_om_mcp.py`](../../tests/unit/test_om_mcp.py) (+ related)

### OMH-ATL (@aravindsai003) — Builder

- [x] `P1-11` Docker: local OM at `:8585` via [`infrastructure/docker-compose.om.yml`](../../infrastructure/docker-compose.om.yml) (server **1.6.2**; not legacy `docker/development/` path)
- [x] `P1-12` Bot JWT: [`scripts/generate_bot_jwt.py`](../../scripts/generate_bot_jwt.py) + `.env` / `make om-gen-token`
- [x] `P1-13` Pre-seed OM: [`seed/customer_db.json`](../../seed/customer_db.json) + [`scripts/load_seed.py`](../../scripts/load_seed.py) (dotenv + `dataLength` for OM 1.6); optional [`scripts/trigger_om_search_reindex.py`](../../scripts/trigger_om_search_reindex.py)
- [x] `P1-14` Confirm React chat UI on `:3000` ([\#27](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/27)): Vite scaffold + [`ui/README.md`](../../ui/README.md) verification checklist + `ui/package-lock.json` + `ui/public/favicon.svg` + `@types/react-dom` aligned to React 18; PR [\#73](https://github.com/GunaPalanivel/openmetadata-mcp-agent/pull/73)
- [x] `P1-15` Document setup: `README.md`, [`docs/getting-started.md`](../../docs/getting-started.md)

### OMH-BSE (@5009226-bhawikakumari) — Delivery

- [x] `P1-16` Write project README.md (1-liner, features, architecture placeholder, setup steps); seed with the AI Disclosure line
- [ ] `P1-17` Daily monitor: [unassigned hackathon GFIs](https://github.com/open-metadata/OpenMetadata/issues?q=is%3Aopen+is%3Aissue+label%3Agood-first-issue+label%3Ahackathon+no%3Aassignee) + ping @PubChimps on OM Slack per [DataFindings/GoodFirstIssues.md](./DataFindings/GoodFirstIssues.md)
- [x] `P1-18` Add AI disclosure to README: "Built with OpenAI GPT-4o-mini via LangGraph + data-ai-sdk"
- [ ] `P1-19` Draft demo narrative outline (refresh [Demo/Narrative.md](./Demo/Narrative.md) with measurable outcomes from [Project/PRD.md](./Project/PRD.md))
- [ ] `P1-20` Daily refresh of [Demo/CompetitiveMatrix.md](./Demo/CompetitiveMatrix.md) — scan #26608, #26645, #26609, #26646 for new artifacts

### Phase 1 Exit Gate

- [/] MCP client **implemented**; live search results require working OM MCP route (**`OM_MCP_HTTP_PATH`**), token, and ES index (see Progress snapshot)
- [x] Chat UI scaffold in repo (`ui/`) with lockfile-driven **`npm ci`** and P1-14 runbook in [`ui/README.md`](../../ui/README.md) (see [\#73](https://github.com/GunaPalanivel/openmetadata-mcp-agent/pull/73))
- [x] README + CLAUDE.md present in new repo
- [/] [Validation/QualityGates.md](./Validation/QualityGates.md) Gate 0 + Gate 1 — verify in CI / locally before demo
- [x] Intent comments posted on #26645 + #26608

---

## Phase 2 — Core Features (Day 5–7: April 21–23)

> **Strategy**: Lead with GOVERNANCE, not search. Auto-classify is our demo opener.

### OMH-GSA (@GunaPalanivel)

- [x] `P2-01` **Auto-classification flow**: classify intent enforces `search_metadata` → `get_entity_details` → `patch_entity` chain with HITL pending_confirmation and seed spot-check columns (`customers.email`, `customers.phone`, `customers.ssn`)
- [ ] `P2-02` **Lineage impact analysis**: NL query → `get_entity_lineage` → GPT translates to human-readable report with Tier warnings
- [ ] `P2-03` Multi-step agent logic: ensure agent can chain 3+ tool calls in one conversation turn
- [x] `P2-04` FastAPI backend: `POST /api/v1/chat` wired to LangGraph agent ([`src/copilot/api/chat.py`](../../src/copilot/api/chat.py))
- [ ] `P2-05` Review all Phase 2 PRs — enforce `PR-Review/Checklist.md`

### OMH-PSTL (@PriyankaSen0902)

- [x] `P2-06` **NL query engine**: text → intent → correct MCP tool → structured Markdown response
- [ ] `P2-07` **Governance summary**: scan catalog → tag coverage %, PII exposure %, unclassified count
- [x] `P2-08` Error handling per [NFRs.md §The 5 Things AI Never Adds](./Project/NFRs.md): retry (`tenacity`) + circuit breaker (`pybreaker`) + structured errors on MCP (`om_mcp.py`); HTTP error envelope middleware in place
- [ ] `P2-09` Integration tests: agent → MCP client → mock OM responses; include circuit-breaker-open paths
- [ ] `P2-10b` Implement `services/prompt_safety.neutralize()` per [Security/PromptInjectionMitigation.md §Layer 1](./Security/PromptInjectionMitigation.md); `tests/security/test_prompt_injection.py` covers all 5 patterns
- [x] `P2-11b` Implement `observability/redact.py` and `middleware/error_envelope.py` per [Security/SecretsHandling.md](./Security/SecretsHandling.md)

### OMH-ATL (@aravindsai003)

- [ ] `P2-10` Connect React UI to FastAPI — real chat responses
- [ ] `P2-11` Render structured responses: tables, tag badges, lineage trees; use `react-markdown` + `rehype-sanitize` (NEVER `dangerouslySetInnerHTML`) per [Architecture/CodingStandards.md](./Architecture/CodingStandards.md)
- [ ] `P2-12` Human-in-the-loop confirmation modal: shows tool name, risk-level badge, summary + entity-FQN list, Confirm/Cancel — per [Architecture/APIContract.md](./Architecture/APIContract.md) `pending_confirmation` envelope
- [ ] `P2-13` E2E test: type query → see result in UI; include the prompt-injection demo flow per [Project/JudgePersona.md §Moment 3](./Project/JudgePersona.md)
- [x] `P2-13b` Build + check in `seed/customer_db.json` (50+ tables incl. PII + Tier1 + 2 prompt-injection planted) per [Demo/FailureRecovery.md §The Frozen Seed Dataset](./Demo/FailureRecovery.md); [`scripts/load_seed.py`](../../scripts/load_seed.py) (+ reindex helper)

### OMH-BSE (@5009226-bhawikakumari)

- [ ] `P2-14` Claim + fix a GFI issue if an unassigned one appears (PR to upstream)
- [ ] `P2-15` Update README with Mermaid architecture diagram (use the trust-boundary diagram from [Architecture/Overview.md](./Architecture/Overview.md))
- [ ] `P2-16` Refresh demo script ([Demo/Narrative.md](./Demo/Narrative.md)) with measurable outcomes from [Project/PRD.md](./Project/PRD.md)
- [ ] `P2-17` Document all 12 MCP tools used in README; cite [DataFindings/ExistingMCPAudit.md §AI SDK Coverage](./DataFindings/ExistingMCPAudit.md) for the 7-typed/5-string-callable split
- [ ] `P2-18` Daily refresh of [Demo/CompetitiveMatrix.md](./Demo/CompetitiveMatrix.md)

### Phase 2b — Governance engine (catalog-backed lifecycle)

> **Spec**: [FeatureDev/GovernanceEngine.md](./FeatureDev/GovernanceEngine.md) — canonical backlog. Informal `P0`–`P6` labels in [Task.md](../../Task.md) are **deprecated for execution**; use the task IDs below. **Merge order** and **16-issue GitHub budget** are in the spec.

- [ ] `P2-19` Session-scoped pending proposals + wire `POST /api/v1/chat/confirm` and `POST /api/v1/chat/cancel` through **services** (replace stubs in [`src/copilot/api/chat.py`](../../src/copilot/api/chat.py))
- [ ] `P2-20` `GovernanceState` + `governance_store` (`transition`, `get_or_create`, in-memory by FQN)
- [ ] `P2-21` Integrate store into LangGraph: `validate_proposal` / `hitl_gate` / confirm path (state transitions)
- [ ] `P2-22` OM write-back: async `patch_entity` custom properties on key transitions (`APPROVED`, `DRIFT_DETECTED`)
- [ ] `P2-23` `drift.py`: lineage hash + tag diff signals vs live OM
- [ ] `P2-24` FastAPI lifespan drift poll + **`GET /api/v1/governance/drift`** ([planned contract](./Architecture/APIContract.md))
- [ ] `P2-25` `similarity.py` + optional opinionated context in `format_response`
- [ ] `P2-26` Causal impact block + `evidence_gap` on `AgentState` / `format_response` (timebox if needed)

### Phase 2 Exit Gate

- [ ] 3 governance workflows working: NL query + auto-classify + lineage impact
- [ ] Chat UI shows real responses from agent
- [ ] Human-in-the-loop confirmation working
- [ ] 30+ tests passing including `tests/security/test_prompt_injection.py`
- [ ] [Validation/QualityGates.md](./Validation/QualityGates.md) Gates 0, 1, 2 (Security), 3 (Resilience) all green for the auto-classify + lineage flows

---

## Phase 3 — Polish + Multi-MCP (Day 8–9: April 24–25)

> **Strategy**: Multi-MCP is our INNOVATION differentiator. Polish UI to OM-native quality.

### OMH-GSA (@GunaPalanivel)

- [ ] `P3-01` **Multi-MCP**: connect GitHub MCP server via `langchain-mcp-adapters`
- [ ] `P3-02` Cross-MCP workflow: "find PII tables → create GitHub issue for each"
- [ ] `P3-03` Governance summary with aggregation: tag coverage %, tier distribution
- [ ] `P3-04` Security audit: no secrets in code, no debug logs, input validation
- [ ] `P3-05` Review all Phase 3 PRs

### OMH-PSTL (@PriyankaSen0902)

- [ ] `P3-06` Edge cases: empty results, auth failure, timeout, ambiguous queries — all surfaced as structured error envelope per [Architecture/APIContract.md](./Architecture/APIContract.md)
- [ ] `P3-07` `structlog` configured with redaction processor + `request_id` propagation per [NFRs.md §NFR-06](./Project/NFRs.md); zero `print()` calls in production code paths (ruff rule T201)
- [ ] `P3-08` Test coverage report: target >70% on `src/copilot/`
- [ ] `P3-09` Add full GitHub Actions CI per [Security/CIHardening.md](./Security/CIHardening.md): lint + typecheck + test-unit + test-integration + security-scan + secret-scan + ui-build; SHA-pinned actions; `permissions: read-all`
- [ ] `P3-09b` Wire `/metrics` endpoint exposing the 4 Golden Signals per [Architecture/APIContract.md §GET /api/v1/metrics](./Architecture/APIContract.md)

### OMH-ATL (@aravindsai003)

- [ ] `P3-10` **OM-native UI**: #7147E8 purple, Inter font, dark mode default
- [ ] `P3-11` Governance dashboard view: tag coverage chart, PII summary cards
- [ ] `P3-12` Responsive layout (judges may view on different screens)
- [ ] `P3-13` Loading animation + error states polished

### OMH-BSE (@5009226-bhawikakumari)

- [ ] `P3-14` Run the 3-rehearsal protocol from [Demo/FailureRecovery.md §Rehearsal protocol](./Demo/FailureRecovery.md): rehearsal 1 happy path, rehearsal 2 with intentional failure at Scene 2, rehearsal 3 on backup machine
- [ ] `P3-15` Record final demo video (2–3 min, 1920×1080); save as `demo/final_recording.mp4`
- [ ] `P3-16` Record + verify backup recording (`demo/backup_recording.mp4`) per [Demo/FailureRecovery.md §The Backup Recording](./Demo/FailureRecovery.md)
- [ ] `P3-17` README finalized: GIF at top, setup in 3 commands, all features listed, AI disclosure, links to Vision Alignment + Architecture + Threat Model
- [ ] `P3-18` Verify clone → run works on a CLEAN machine using [Validation/SetupGuide.md](./Validation/SetupGuide.md)
- [ ] `P3-19` Architecture diagram + trust boundary diagram (Mermaid) embedded in README

### Phase 3 Exit Gate

- [ ] Multi-MCP workflow demonstrated
- [ ] UI is OM-native quality (`#7147E8` purple, Inter, dark mode default)
- [ ] Final + backup demo videos recorded; both play cleanly
- [ ] README clone → run < 5 min on the backup machine
- [ ] All tests green, >70% coverage on `src/copilot/`
- [ ] [Validation/QualityGates.md](./Validation/QualityGates.md) Gates 0, 1, 2, 3, 4 (Observability), 5 (AI/ML Security) all green

---

## Phase 4 — Submit (Day 10: April 26)

### All Team

- [ ] `P4-00` 🔴 Run the [Validation/PRR.md](./Validation/PRR.md) Production Readiness Review checklist end-to-end (OMH-GSA owns; sign-off recorded in PRR.md)
- [ ] `P4-01` Final README review (OMH-BSE)
- [ ] `P4-02` Repo hygiene: `.gitignore`, no `.env`, no debug code, `gitleaks detect` returns 0 findings (OMH-GSA)
- [ ] `P4-03` AI disclosure in README confirmed (OMH-BSE)
- [ ] `P4-03b` Produce final security audit report `openmetadata-mcp-agent/SECURITY_AUDIT_2026-04-25.md` per [security-vulnerability-auditor SKILL §Phase 6](../agents/security-vulnerability-auditor/SKILL.md); mark every SC-N from [Security/ThreatModel.md](./Security/ThreatModel.md) as `verified | contradicted | unverified` (OMH-GSA)
- [ ] `P4-03c` Run [Demo/FailureRecovery.md §Pre-conditions](./Demo/FailureRecovery.md) checklist on demo machine the night before (OMH-ATL)
- [ ] `P4-04` Submit hackathon form on WeMakeDevs (OMH-GSA)
- [ ] `P4-05` Link demo video + repo in submission (OMH-GSA)
- [ ] `P4-06` Verify GFI PR status (OMH-BSE)
- [ ] `P4-07` Comment on #26645 + #26608 with submission link (OMH-GSA)
- [ ] `P4-08` Team retrospective within 48h (all)

---

## ⚖️ Scoring Checklist (Run Before P4-04)

| Criterion                | Check                                                                                                           | Score Target |
| ------------------------ | --------------------------------------------------------------------------------------------------------------- | ------------ |
| Potential Impact         | Demo shows real governance automation (not just search)                                                         | 9/10         |
| Creativity & Innovation  | Multi-MCP + LLM classification shown                                                                            | 9/10         |
| Technical Excellence     | Tests pass, logging present, error handling, CI green                                                           | 8/10         |
| Best Use of OpenMetadata | All 12 MCP tools exercised end-to-end (7 via SDK's typed `MCPTool` enum + 5 via `client.mcp.call_tool` by name) | 10/10        |
| User Experience          | OM-native UI, human-in-the-loop, structured responses                                                           | 8/10         |
| Presentation Quality     | README has GIF, Mermaid diagram, <3 min setup; demo is narrated                                                 | 8/10         |

---

## Task Status Legend

| Symbol | Meaning             |
| ------ | ------------------- |
| `[ ]`  | Not started         |
| `[/]`  | In progress         |
| `[x]`  | Completed           |
| `[!]`  | Blocked             |
| 🔴     | Critical — do TODAY |
