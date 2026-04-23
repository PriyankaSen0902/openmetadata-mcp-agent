# TaskSync — Master Task Tracker

> **Last updated**: April 19, 2026 (Day 3)
> **LLM Provider**: ✅ OpenAI GPT-4o-mini (free Codex credits)
> **Repo Strategy**: ✅ NEW standalone repo (`openmetadata-mcp-agent`) + fork for GFI only
> **Plan/ location**: ✅ `.idea/Plan/` stays local (agent command center)
> **All tasks ordered by priority. Check off as you complete them.**

---

## Phase 0 — Claim & Setup (IMMEDIATE — Today April 19)

> ⚠️ **No formal assignment**: Per @PubChimps's Apr 18, 2026 comments on [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) and [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608): _"We will not be assigning this issue, this is just an idea of something that could be submitted for it!"_ Hackathon ideas are open competition — comment to **signal coordination**, not to claim. Build & submit regardless.

### OMH-GSA (@GunaPalanivel) — CRITICAL

- [ ] `P0-01` 🔴 Post intent comment on [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) (Multi-MCP Orchestrator) and start building immediately — competing prototypes already exist (@0xSaksham LangGraph, @MonotonousHarsh, @afifasyed123)
- [ ] `P0-02` 🔴 Post intent comment on [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608) (Chat App) and start building immediately — @thisisvaishnav already shared a [working Loom demo](https://www.loom.com/share/c2fc5f9fb9314c279faa1fc9967576f3) using Claude + MCP tool chaining
- [ ] `P0-03` Create NEW repo: `GunaPalanivel/openmetadata-mcp-agent` on GitHub (public, Apache 2.0)
- [ ] `P0-04` Redeem OpenAI API credits at platform.openai.com/promotions
- [ ] `P0-05` Generate OpenAI API key, save in `.env`
- [ ] `P0-06` Add all team as collaborators: @PriyankaSen0902, @aravindsai003, @5009226-bhawikakumari
- [ ] `P0-07` Drop the `CLAUDE.md` template from [Architecture/CLAUDETemplate.md](./Architecture/CLAUDETemplate.md) into the new repo root so all future AI sessions inherit the architectural contract
- [ ] `P0-08` Star [open-metadata/OpenMetadata](https://github.com/open-metadata/OpenMetadata) — hackathon side-quest requirement (all 4 team members)
- [ ] `P0-09` Read [Project/Discovery.md](./Project/Discovery.md), [Project/NFRs.md](./Project/NFRs.md), [Architecture/CodingStandards.md](./Architecture/CodingStandards.md), and [Security/PromptInjectionMitigation.md](./Security/PromptInjectionMitigation.md) — every team member, before writing any code (45 min total)
- [ ] `P0-10` Every team member: after `make install_dev_env`, run `pip install pre-commit && pre-commit install && pre-commit run --all-files`. Same hooks as CI; commits that skip them will fail PR review. See [Validation/SetupGuide.md §Step 4b](./Validation/SetupGuide.md) and [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

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

- [ ] `P1-01` Init `openmetadata-mcp-agent` repo with `pyproject.toml`
  - Deps (Phase 1): `data-ai-sdk[langchain]`, `langchain-openai`, `langgraph`, `fastapi`, `uvicorn`
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
- [ ] `P1-03` Implement MCP client (`mcp_client.py`): connect to OM, call `search_metadata`
- [ ] `P1-04` Build LangGraph agent skeleton: NL input → intent classify → tool select → respond
- [ ] `P1-05` Verify: `python -c "from copilot.mcp_client import ...; search('tables')"` returns data
- [ ] `P1-06` Review all Phase 1 PRs from team

### OMH-PSTL (@PriyankaSen0902) — Senior Builder

- [ ] `P1-07` Study `data-ai-sdk` + `langchain-openai` docs — document tool schemas
- [ ] `P1-08` Map all 12 MCP tools to governance use-cases → update `ExistingMCPAudit.md`. Split: **7 typed enum tools** (`SEARCH_METADATA`, `GET_ENTITY_DETAILS`, `GET_ENTITY_LINEAGE`, `CREATE_GLOSSARY`, `CREATE_GLOSSARY_TERM`, `CREATE_LINEAGE`, `PATCH_ENTITY`) reachable via `MCPTool.X`; **5 string-callable tools** (`semantic_search`, `get_test_definitions`, `create_test_case`, `create_metric`, `root_cause_analysis`) reachable via `client.mcp.call_tool("name", args)`
- [ ] `P1-09` Create typed wrapper for top 6 tools (Pydantic models for params + responses)
- [ ] `P1-10` Write 10+ unit tests for MCP client wrapper (mock responses)

### OMH-ATL (@aravindsai003) — Builder

- [ ] `P1-11` Docker: get local OM instance running at `:8585` (use `docker/development/`)
- [ ] `P1-12` Verify Swagger at `localhost:8585/swagger.html`, generate Bot JWT
- [ ] `P1-13` Pre-seed OM with **50+ realistic tables** (use sample data or CSV import)
- [ ] `P1-14` Scaffold React chat UI (Vite + React)
- [ ] `P1-15` Document setup in `README.md` — must be clone → run in <5 min

### OMH-BSE (@5009226-bhawikakumari) — Delivery

- [ ] `P1-16` Write project README.md (1-liner, features, architecture placeholder, setup steps); seed with the AI Disclosure line
- [ ] `P1-17` Daily monitor: [unassigned hackathon GFIs](https://github.com/open-metadata/OpenMetadata/issues?q=is%3Aopen+is%3Aissue+label%3Agood-first-issue+label%3Ahackathon+no%3Aassignee) + ping @PubChimps on OM Slack per [DataFindings/GoodFirstIssues.md](./DataFindings/GoodFirstIssues.md)
- [ ] `P1-18` Add AI disclosure to README: "Built with OpenAI GPT-4o-mini via LangGraph + data-ai-sdk"
- [ ] `P1-19` Draft demo narrative outline (refresh [Demo/Narrative.md](./Demo/Narrative.md) with measurable outcomes from [Project/PRD.md](./Project/PRD.md))
- [ ] `P1-20` Daily refresh of [Demo/CompetitiveMatrix.md](./Demo/CompetitiveMatrix.md) — scan #26608, #26645, #26609, #26646 for new artifacts

### Phase 1 Exit Gate

- [ ] MCP client connects and returns search results
- [ ] Chat UI scaffold renders on localhost
- [ ] README + CLAUDE.md present in new repo
- [ ] [Validation/QualityGates.md](./Validation/QualityGates.md) Gate 0 (automated checks) + Gate 1 (Architecture Integrity) all green
- [ ] Intent comments posted on #26645 + #26608

---

## Phase 2 — Core Features (Day 5–7: April 21–23)

> **Strategy**: Lead with GOVERNANCE, not search. Auto-classify is our demo opener.

### OMH-GSA (@GunaPalanivel)

- [ ] `P2-01` **Auto-classification flow**: scan tables → GPT-4o-mini classifies columns → suggest PII tags → user confirms → `patch_entity` applies
- [ ] `P2-02` **Lineage impact analysis**: NL query → `get_entity_lineage` → GPT translates to human-readable report with Tier warnings
- [ ] `P2-03` Multi-step agent logic: ensure agent can chain 3+ tool calls in one conversation turn
- [ ] `P2-04` FastAPI backend: `POST /chat` endpoint wired to LangGraph agent
- [ ] `P2-05` Review all Phase 2 PRs — enforce `PR-Review/Checklist.md`

### OMH-PSTL (@PriyankaSen0902)

- [x] `P2-06` **NL query engine**: text → intent → correct MCP tool → structured Markdown response
- [ ] `P2-07` **Governance summary**: scan catalog → tag coverage %, PII exposure %, unclassified count
- [ ] `P2-08` Error handling per [NFRs.md §The 5 Things AI Never Adds](./Project/NFRs.md): retry (`tenacity`) + circuit breaker (`pybreaker`) + structured error envelope on every MCP call
- [ ] `P2-09` Integration tests: agent → MCP client → mock OM responses; include circuit-breaker-open paths
- [ ] `P2-10b` Implement `services/prompt_safety.neutralize()` per [Security/PromptInjectionMitigation.md §Layer 1](./Security/PromptInjectionMitigation.md); `tests/security/test_prompt_injection.py` covers all 5 patterns
- [ ] `P2-11b` Implement `observability/redact.py` and `middleware/error_envelope.py` per [Security/SecretsHandling.md](./Security/SecretsHandling.md)

### OMH-ATL (@aravindsai003)

- [ ] `P2-10` Connect React UI to FastAPI — real chat responses
- [ ] `P2-11` Render structured responses: tables, tag badges, lineage trees; use `react-markdown` + `rehype-sanitize` (NEVER `dangerouslySetInnerHTML`) per [Architecture/CodingStandards.md](./Architecture/CodingStandards.md)
- [ ] `P2-12` Human-in-the-loop confirmation modal: shows tool name, risk-level badge, summary + entity-FQN list, Confirm/Cancel — per [Architecture/APIContract.md](./Architecture/APIContract.md) `pending_confirmation` envelope
- [ ] `P2-13` E2E test: type query → see result in UI; include the prompt-injection demo flow per [Project/JudgePersona.md §Moment 3](./Project/JudgePersona.md)
- [ ] `P2-13b` Build + check in `seed/customer_db.json` (50+ tables incl. PII + Tier1 + 2 prompt-injection planted) per [Demo/FailureRecovery.md §The Frozen Seed Dataset](./Demo/FailureRecovery.md); write `scripts/load_seed.py`

### OMH-BSE (@5009226-bhawikakumari)

- [ ] `P2-14` Claim + fix a GFI issue if an unassigned one appears (PR to upstream)
- [ ] `P2-15` Update README with Mermaid architecture diagram (use the trust-boundary diagram from [Architecture/Overview.md](./Architecture/Overview.md))
- [ ] `P2-16` Refresh demo script ([Demo/Narrative.md](./Demo/Narrative.md)) with measurable outcomes from [Project/PRD.md](./Project/PRD.md)
- [ ] `P2-17` Document all 12 MCP tools used in README; cite [DataFindings/ExistingMCPAudit.md §AI SDK Coverage](./DataFindings/ExistingMCPAudit.md) for the 7-typed/5-string-callable split
- [ ] `P2-18` Daily refresh of [Demo/CompetitiveMatrix.md](./Demo/CompetitiveMatrix.md)

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
