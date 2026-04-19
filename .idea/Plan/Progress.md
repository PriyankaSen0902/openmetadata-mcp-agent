# Progress Tracker

Per-person, per-phase progress on every task in [TaskSync.md](./TaskSync.md). One row per task. Use this file to coordinate day to day.

## How to use this file

1. Pick the next task in the "Order of execution" list for your phase.
2. Open a GitHub issue for that task in `GunaPalanivel/openmetadata-mcp-agent` using the right template (`task`, `feature`, or `bug`). Title format: `[<TASK-ID>] <short description>` (for example, `[P1-03] MCP client: search_metadata happy path`).
3. Assign the issue to yourself. Paste the issue number into the `Issue` column below.
4. Create a branch: `<type>/<task-id>-<short-slug>` (for example, `feat/p1-03-mcp-client-search`).
5. Walk the lifecycle and tick the boxes as you go. Do not check `Merged` until the PR is squashed and merged into `main`.

## Reviewer routing (automatic)

PRs get a reviewer requested for you by `.github/workflows/auto-assign-reviewer.yml`:

| Author | Reviewer requested |
| --- | --- |
| @PriyankaSen0902, @aravindsai003, @5009226-bhawikakumari | @GunaPalanivel |
| @GunaPalanivel | @PriyankaSen0902 |
| Outside contributor (forks, community) | @PriyankaSen0902 |

Backup: `.github/CODEOWNERS` requests @GunaPalanivel by default if the workflow is disabled.

## Lifecycle checklist (one row per task)

Each row uses the same 8-step lifecycle. Check the boxes inline:

```
[P] Plan  [B] Build  [V1] Validate  [F] Fix  [V2] Validate  [PR] PR opened  [R] Reviewed  [M] Merged
```

## Status legend

| Symbol | Meaning |
| --- | --- |
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Done |
| `[!]` | Blocked (add a note next to the row) |

---

## Phase 0 — Claim and Setup (Day 3, April 19)

**Order of execution:** P0-01 → P0-02 → P0-03 → P0-04 → P0-05 → P0-06 → P0-07 → P0-08 → P0-09 → P0-10 (P0-10 is per-person, every contributor must finish it before their first commit).

### @GunaPalanivel

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | Post intent comment on upstream #26645 | upstream | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-02 | Post intent comment on upstream #26608 | upstream | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-03 | Create repo `GunaPalanivel/openmetadata-mcp-agent` | done | n/a | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| P0-04 | Redeem OpenAI API credits | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-05 | Generate OpenAI API key, save in `.env` | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-06 | Add team as collaborators (3 invites) | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-07 | Drop `CLAUDE.md` template into repo root | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-08 | Star `open-metadata/OpenMetadata` (all 4) | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P0-09 | Read Discovery + NFRs + CodingStandards + PromptInjection | #__ | n/a | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| P0-10 | Install pre-commit hooks (`pre-commit install` + `run --all-files`) | n/a | n/a | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |

### Per-person setup (every contributor)

| Owner | P0-10 Install pre-commit hooks |
| --- | --- |
| @GunaPalanivel | [x] |
| @PriyankaSen0902 | [ ] |
| @aravindsai003 | [ ] |
| @5009226-bhawikakumari | [ ] |

---

## Phase 1 — Foundation (Day 3 to 4, April 19 to 20)

**Order of execution (cross-team):**

1. P1-11 (ATL: Docker OM running) — unblocks integration testing.
2. P1-01 → P1-02 (GSA: project skeleton + deps) — unblocks everyone else.
3. P1-07 → P1-08 → P1-09 (PSTL: SDK study + tool map + typed wrappers) — feeds GSA's agent.
4. P1-03 → P1-04 → P1-05 (GSA: MCP client + agent skeleton + verify).
5. P1-12 → P1-13 (ATL: Swagger/Bot JWT + seed 50+ tables).
6. P1-14 (ATL: scaffold React UI).
7. P1-10 (PSTL: 10+ unit tests for MCP wrapper).
8. P1-15 (ATL: README setup steps).
9. P1-16 → P1-18 (BSE: README + AI disclosure).
10. P1-17 → P1-19 → P1-20 (BSE: GFI watch + demo narrative + competitive matrix).
11. P1-06 (GSA: review all Phase 1 PRs).

### @GunaPalanivel

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1-01 | Init repo with `pyproject.toml` and Phase 1 deps | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-02 | Create project structure (`src/copilot/...`, `ui/`, `tests/`) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-03 | Implement MCP client `search_metadata` happy path | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-04 | LangGraph agent skeleton (NL → intent → tool → respond) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-05 | Verify smoke: search returns data | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-06 | Review all Phase 1 PRs | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @PriyankaSen0902

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1-07 | Study `data-ai-sdk` + `langchain-openai`, document tool schemas | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-08 | Map all 12 MCP tools to governance use cases (update audit doc) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-09 | Typed wrapper for top 6 tools (Pydantic params + responses) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-10 | 10+ unit tests for MCP client wrapper (mock responses) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @aravindsai003

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1-11 | Local OM at `:8585` via `docker/development/` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-12 | Verify Swagger; generate Bot JWT | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-13 | Pre-seed OM with 50+ realistic tables | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-14 | Scaffold React chat UI (Vite + React) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-15 | Document setup in `README.md` (clone to run in 5 min) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @5009226-bhawikakumari

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1-16 | Write project `README.md` (1-liner, features, setup) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-17 | Daily monitor unassigned hackathon GFIs | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-18 | Add AI disclosure to `README.md` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-19 | Draft demo narrative outline (refresh `Demo/Narrative.md`) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P1-20 | Daily refresh `Demo/CompetitiveMatrix.md` | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### Phase 1 Exit Gate

- [ ] MCP client connects and returns search results
- [ ] Chat UI scaffold renders on localhost
- [ ] `README.md` and `CLAUDE.md` present in repo
- [ ] `Validation/QualityGates.md` Gate 0 + Gate 1 green
- [ ] Intent comments posted on #26645 + #26608

---

## Phase 2 — Core Features (Day 5 to 7, April 21 to 23)

**Order of execution (cross-team):**

1. P2-08 (PSTL: error envelope + retry/breaker on every MCP call) — foundation for the rest.
2. P2-11b (PSTL: redact + error envelope middleware).
3. P2-13b (ATL: load `seed/customer_db.json` with 50+ tables and 2 prompt-injection planted).
4. P2-01 (GSA: auto-classification flow).
5. P2-02 (GSA: lineage impact analysis).
6. P2-03 (GSA: 3+ tool-call chaining in one turn).
7. P2-04 (GSA: `POST /chat` wired to LangGraph agent).
8. P2-06 → P2-07 (PSTL: NL query engine + governance summary).
9. P2-10b (PSTL: prompt-safety neutralize + 5-pattern test file).
10. P2-09 (PSTL: integration tests including circuit-breaker-open).
11. P2-10 → P2-11 → P2-12 → P2-13 (ATL: UI to API + structured render + HITL modal + E2E).
12. P2-14 → P2-15 → P2-16 → P2-17 → P2-18 (BSE: GFI PR + Mermaid diagram + narrative + 12-tool doc + matrix).
13. P2-05 (GSA: review all Phase 2 PRs against the full checklist).

### @GunaPalanivel

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2-01 | Auto-classification: scan + LLM classify + HITL + `patch_entity` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-02 | Lineage impact analysis report with Tier warnings | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-03 | Multi-step agent: chain 3+ tool calls per turn | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-04 | FastAPI `POST /chat` wired to LangGraph agent | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-05 | Review all Phase 2 PRs (full PR-Review checklist) | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @PriyankaSen0902

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2-06 | NL query engine: text → intent → tool → Markdown | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-07 | Governance summary: tag coverage %, PII %, unclassified count | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-08 | Retry + circuit breaker + structured error envelope on MCP calls | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-09 | Integration tests including circuit-breaker-open paths | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-10b | `services/prompt_safety.neutralize` + 5-pattern test file | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-11b | `observability/redact.py` + `middleware/error_envelope.py` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @aravindsai003

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2-10 | Connect React UI to FastAPI (real chat responses) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-11 | Render structured responses (markdown + sanitize, no innerHTML) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-12 | HITL confirmation modal (tool name, risk, FQN list, Confirm/Cancel) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-13 | E2E test including the prompt-injection demo flow | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-13b | Build + commit `seed/customer_db.json` and `scripts/load_seed.py` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @5009226-bhawikakumari

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2-14 | Claim + fix a GFI issue if an unassigned one appears | upstream | upstream | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-15 | README Mermaid architecture + trust-boundary diagram | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-16 | Refresh `Demo/Narrative.md` with measurable outcomes | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-17 | Document all 12 MCP tools used in README (cite audit) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P2-18 | Daily refresh `Demo/CompetitiveMatrix.md` | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### Phase 2 Exit Gate

- [ ] 3 governance workflows working: NL query + auto-classify + lineage impact
- [ ] Chat UI shows real responses from agent
- [ ] HITL confirmation working
- [ ] 30+ tests passing including `tests/security/test_prompt_injection.py`
- [ ] `Validation/QualityGates.md` Gates 0, 1, 2, 3 green for the auto-classify + lineage flows

---

## Phase 3 — Polish + Multi-MCP (Day 8 to 9, April 24 to 25)

**Order of execution (cross-team):**

1. P3-01 → P3-02 (GSA: GitHub MCP + cross-MCP workflow).
2. P3-03 (GSA: governance summary aggregation).
3. P3-06 (PSTL: edge cases as structured envelope).
4. P3-07 (PSTL: structlog with redact + request_id).
5. P3-09b (PSTL: `/metrics` endpoint with 4 Golden Signals).
6. P3-09 (PSTL: full hardened CI per `Security/CIHardening.md`).
7. P3-08 (PSTL: coverage report >70% on `src/copilot/`).
8. P3-10 → P3-11 → P3-12 → P3-13 (ATL: OM-native UI + dashboard + responsive + states).
9. P3-04 (GSA: security audit pass).
10. P3-14 (BSE: 3-rehearsal protocol).
11. P3-15 → P3-16 (BSE: final + backup demo recordings).
12. P3-17 → P3-18 → P3-19 (BSE: README finalize + clean-machine verify + diagrams).
13. P3-05 (GSA: review all Phase 3 PRs).

### @GunaPalanivel

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-01 | Multi-MCP: connect GitHub MCP via `langchain-mcp-adapters` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-02 | Cross-MCP: find PII tables → open GitHub issue per table | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-03 | Governance summary aggregation (coverage + tier distribution) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-04 | Security audit (no secrets, no debug logs, input validation) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-05 | Review all Phase 3 PRs | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @PriyankaSen0902

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-06 | Edge cases as structured error envelope | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-07 | structlog + redact processor + request_id propagation; no `print()` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-08 | Coverage report >70% on `src/copilot/` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-09 | Full hardened GitHub Actions CI per `Security/CIHardening.md` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-09b | `/metrics` endpoint exposing the 4 Golden Signals | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @aravindsai003

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-10 | OM-native UI (`#7147E8`, Inter font, dark mode default) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-11 | Governance dashboard (tag coverage chart, PII summary cards) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-12 | Responsive layout for judging on different screens | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-13 | Loading + error states polished | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### @5009226-bhawikakumari

| Task ID | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-14 | Run the 3-rehearsal protocol | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-15 | Record `demo/final_recording.mp4` (2 to 3 min, 1920x1080) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-16 | Record + verify `demo/backup_recording.mp4` | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-17 | Finalize README (GIF top, 3-cmd setup, AI disclosure, links) | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-18 | Verify clone-to-run on a clean machine | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P3-19 | Architecture + trust-boundary Mermaid embedded in README | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### Phase 3 Exit Gate

- [ ] Multi-MCP workflow demonstrated
- [ ] UI is OM-native quality (`#7147E8`, Inter, dark mode default)
- [ ] Final + backup demo videos recorded; both play cleanly
- [ ] README clone-to-run < 5 min on the backup machine
- [ ] All tests green, >70% coverage on `src/copilot/`
- [ ] `Validation/QualityGates.md` Gates 0, 1, 2, 3, 4, 5 green

---

## Phase 4 — Submit (Day 10, April 26)

**Order of execution (mostly @GunaPalanivel and @5009226-bhawikakumari):**

1. P4-00 (GSA: PRR end-to-end).
2. P4-01 (BSE: final README review).
3. P4-02 (GSA: repo hygiene + `gitleaks detect`).
4. P4-03 (BSE: confirm AI disclosure).
5. P4-03b (GSA: final security audit report).
6. P4-03c (ATL: pre-conditions checklist on demo machine).
7. P4-04 → P4-05 (GSA: submit hackathon form + link demo + repo).
8. P4-06 (BSE: verify GFI PR status).
9. P4-07 (GSA: comment submission link on #26645 + #26608).
10. P4-08 (All: retrospective within 48h).

### All team

| Task ID | Owner | Description | Issue | PR | P | B | V1 | F | V2 | PR opened | R | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P4-00 | @GunaPalanivel | Run `Validation/PRR.md` PRR checklist end-to-end | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-01 | @5009226-bhawikakumari | Final README review | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-02 | @GunaPalanivel | Repo hygiene + `gitleaks detect` returns 0 findings | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-03 | @5009226-bhawikakumari | AI disclosure confirmed in README | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-03b | @GunaPalanivel | `SECURITY_AUDIT_2026-04-25.md` with SC-N status | #__ | #__ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-03c | @aravindsai003 | Demo machine pre-conditions checklist | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-04 | @GunaPalanivel | Submit hackathon form on WeMakeDevs | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-05 | @GunaPalanivel | Link demo video + repo in submission | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-06 | @5009226-bhawikakumari | Verify GFI PR status | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-07 | @GunaPalanivel | Comment submission link on #26645 + #26608 | upstream | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P4-08 | All | Team retrospective within 48h | #__ | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## Snapshot per person (counts so far)

| Owner | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Total |
| --- | --- | --- | --- | --- | --- | --- |
| @GunaPalanivel | 9 | 6 | 5 | 5 | 6 | 31 |
| @PriyankaSen0902 | 0 | 4 | 6 | 5 | 0 | 15 |
| @aravindsai003 | 0 | 5 | 5 | 4 | 1 | 15 |
| @5009226-bhawikakumari | 0 | 5 | 5 | 6 | 3 | 19 |

Update the counts above only if you add or remove rows.
