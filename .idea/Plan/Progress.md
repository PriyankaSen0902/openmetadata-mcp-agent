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

| Author                                                   | Reviewer requested |
| -------------------------------------------------------- | ------------------ |
| @PriyankaSen0902, @aravindsai003, @5009226-bhawikakumari | @GunaPalanivel     |
| @GunaPalanivel                                           | @PriyankaSen0902   |
| Outside contributor (forks, community)                   | @PriyankaSen0902   |

Backup: `.github/CODEOWNERS` requests @GunaPalanivel by default if the workflow is disabled.

## Lifecycle checklist (one row per task)

Each row uses the same 8-step lifecycle. Check the boxes inline:

```
[P] Plan  [B] Build  [V1] Validate  [F] Fix  [V2] Validate  [PR] PR opened  [R] Reviewed  [M] Merged
```

## Status legend

| Symbol | Meaning                              |
| ------ | ------------------------------------ |
| `[ ]`  | Not started                          |
| `[/]`  | In progress                          |
| `[x]`  | Done                                 |
| `[!]`  | Blocked (add a note next to the row) |

---

## Phase 0 — Claim and Setup (Day 3, April 19)

**Order of execution:** P0-01 → P0-02 → P0-03 → P0-04 → P0-05 → P0-06 → P0-07 → P0-08 → P0-09 → P0-10 (P0-10 is per-person, every contributor must finish it before their first commit).

### @GunaPalanivel

| Task ID | Description                                                         | Issue                                                                                                | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P0-01   | Post intent comment on upstream #26645                              | [#26645 comment](https://github.com/open-metadata/OpenMetadata/issues/26645#issuecomment-4275961194) | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-02   | Post intent comment on upstream #26608                              | [#26608 comment](https://github.com/open-metadata/OpenMetadata/issues/26608#issuecomment-4275961984) | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-03   | Create repo `GunaPalanivel/openmetadata-mcp-agent`                  | done                                                                                                 | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-04   | Redeem OpenAI API credits (deferred until P2-01)                    | n/a                                                                                                  | n/a   | [!] | [!] | [!] | [!] | [!] | [!]       | [!] | [!] |
| P0-05   | Generate OpenAI API key, save in `.env` (deferred with P0-04)       | n/a                                                                                                  | n/a   | [!] | [!] | [!] | [!] | [!] | [!]       | [!] | [!] |
| P0-06   | Add team as collaborators (3 invites)                               | done                                                                                                 | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-07   | Drop `CLAUDE.md` template into repo root                            | done                                                                                                 | done  | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-08   | Star `open-metadata/OpenMetadata` (all 4)                           | done                                                                                                 | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-09   | Read Discovery + NFRs + CodingStandards + PromptInjection           | #\_\_                                                                                                | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |
| P0-10   | Install pre-commit hooks (`pre-commit install` + `run --all-files`) | n/a                                                                                                  | n/a   | [x] | [x] | [x] | [x] | [x] | [x]       | [x] | [x] |

### Per-person setup (every contributor)

| Owner                  | P0-10 Install pre-commit hooks |
| ---------------------- | ------------------------------ |
| @GunaPalanivel         | [x]                            |
| @PriyankaSen0902       | [ ]                            |
| @aravindsai003         | [ ]                            |
| @5009226-bhawikakumari | [ ]                            |

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

| Task ID | Description                                                   | Issue                                                                       | PR  | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------- | --------------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P1-01   | Init repo with `pyproject.toml` and Phase 1 deps              | [#14](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/14)    |     | [x] | [x] | [x] | [x] | [x] | [x]       | [ ] | [ ] |
| P1-02   | Create project structure (`src/copilot/...`, `ui/`, `tests/`) | [#15](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/15)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-03   | Implement MCP client `search_metadata` happy path             | [#16](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/16)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-04   | LangGraph agent skeleton (NL -> intent -> tool -> respond)    | [#17](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/17)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-05   | Verify smoke: search returns data                             | [#18](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/18)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-06   | Review all Phase 1 PRs                                        | [#19](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/19)    | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @PriyankaSen0902

| Task ID | Description                                                     | Issue                                                                       | PR  | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | --------------------------------------------------------------- | --------------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P1-07   | Study `data-ai-sdk` + `langchain-openai`, document tool schemas | [#20](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/20)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-08   | Map all 12 MCP tools to governance use cases (update audit doc) | [#21](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/21)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-09   | Typed wrapper for top 6 tools (Pydantic params + responses)     | [#22](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/22)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-10   | 10+ unit tests for MCP client wrapper (mock responses)          | [#23](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/23)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @aravindsai003

| Task ID | Description                                           | Issue                                                                       | PR  | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ----------------------------------------------------- | --------------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P1-11   | Local OM at `:8585` via `docker/development/`         | [#24](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/24)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-12   | Generate Bot JWT, share privately                     | [#25](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/25)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-13   | Pre-seed OM with 50+ realistic tables                 | [#26](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/26)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-14   | Confirm UI scaffold runs on `:3000`                   | [#27](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/27)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-15   | Document setup in `README.md` (clone to run in 5 min) | [#28](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/28)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @5009226-bhawikakumari

| Task ID | Description                                                | Issue                                                                       | PR  | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ---------------------------------------------------------- | --------------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P1-16   | Polish public README (1-liner, features, setup)            | [#29](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/29)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-17   | Daily monitor unassigned hackathon GFIs                    | [#30](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/30)    | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-18   | Add AI disclosure to `README.md`                           | [#31](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/31)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-19   | Draft demo narrative outline (refresh `Demo/Narrative.md`) | [#32](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/32)    |     | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P1-20   | Daily refresh `Demo/CompetitiveMatrix.md`                  | [#33](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/33)    | n/a | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

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

| Task ID | Description                                                      | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ---------------------------------------------------------------- | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P2-01   | Auto-classification: scan + LLM classify + HITL + `patch_entity` | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-02   | Lineage impact analysis report with Tier warnings                | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-03   | Multi-step agent: chain 3+ tool calls per turn                   | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-04   | FastAPI `POST /chat` wired to LangGraph agent                    | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-05   | Review all Phase 2 PRs (full PR-Review checklist)                | #\_\_ | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @PriyankaSen0902

| Task ID | Description                                                      | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ---------------------------------------------------------------- | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P2-06   | NL query engine: text → intent → tool → Markdown                 | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-07   | Governance summary: tag coverage %, PII %, unclassified count    | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-08   | Retry + circuit breaker + structured error envelope on MCP calls | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-09   | Integration tests including circuit-breaker-open paths           | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-10b  | `services/prompt_safety.neutralize` + 5-pattern test file        | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-11b  | `observability/redact.py` + `middleware/error_envelope.py`       | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @aravindsai003

| Task ID | Description                                                         | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------------- | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P2-10   | Connect React UI to FastAPI (real chat responses)                   | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-11   | Render structured responses (markdown + sanitize, no innerHTML)     | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-12   | HITL confirmation modal (tool name, risk, FQN list, Confirm/Cancel) | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-13   | E2E test including the prompt-injection demo flow                   | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-13b  | Build + commit `seed/customer_db.json` and `scripts/load_seed.py`   | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @5009226-bhawikakumari

| Task ID | Description                                           | Issue    | PR       | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ----------------------------------------------------- | -------- | -------- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P2-14   | Claim + fix a GFI issue if an unassigned one appears  | upstream | upstream | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-15   | README Mermaid architecture + trust-boundary diagram  | #\_\_    | #\_\_    | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-16   | Refresh `Demo/Narrative.md` with measurable outcomes  | #\_\_    | #\_\_    | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-17   | Document all 12 MCP tools used in README (cite audit) | #\_\_    | #\_\_    | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P2-18   | Daily refresh `Demo/CompetitiveMatrix.md`             | #\_\_    | n/a      | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

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

| Task ID | Description                                                   | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------- | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P3-01   | Multi-MCP: connect GitHub MCP via `langchain-mcp-adapters`    | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-02   | Cross-MCP: find PII tables → open GitHub issue per table      | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-03   | Governance summary aggregation (coverage + tier distribution) | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-04   | Security audit (no secrets, no debug logs, input validation)  | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-05   | Review all Phase 3 PRs                                        | #\_\_ | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @PriyankaSen0902

| Task ID | Description                                                         | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------------- | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P3-06   | Edge cases as structured error envelope                             | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-07   | structlog + redact processor + request_id propagation; no `print()` | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-08   | Coverage report >70% on `src/copilot/`                              | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-09   | Full hardened GitHub Actions CI per `Security/CIHardening.md`       | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-09b  | `/metrics` endpoint exposing the 4 Golden Signals                   | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @aravindsai003

| Task ID | Description                                                  | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------ | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P3-10   | OM-native UI (`#7147E8`, Inter font, dark mode default)      | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-11   | Governance dashboard (tag coverage chart, PII summary cards) | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-12   | Responsive layout for judging on different screens           | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-13   | Loading + error states polished                              | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

### @5009226-bhawikakumari

| Task ID | Description                                                  | Issue | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ------------------------------------------------------------ | ----- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P3-14   | Run the 3-rehearsal protocol                                 | #\_\_ | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-15   | Record `demo/final_recording.mp4` (2 to 3 min, 1920x1080)    | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-16   | Record + verify `demo/backup_recording.mp4`                  | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-17   | Finalize README (GIF top, 3-cmd setup, AI disclosure, links) | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-18   | Verify clone-to-run on a clean machine                       | #\_\_ | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P3-19   | Architecture + trust-boundary Mermaid embedded in README     | #\_\_ | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

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

| Task ID | Owner                  | Description                                         | Issue    | PR    | P   | B   | V1  | F   | V2  | PR opened | R   | M   |
| ------- | ---------------------- | --------------------------------------------------- | -------- | ----- | --- | --- | --- | --- | --- | --------- | --- | --- |
| P4-00   | @GunaPalanivel         | Run `Validation/PRR.md` PRR checklist end-to-end    | #\_\_    | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-01   | @5009226-bhawikakumari | Final README review                                 | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-02   | @GunaPalanivel         | Repo hygiene + `gitleaks detect` returns 0 findings | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-03   | @5009226-bhawikakumari | AI disclosure confirmed in README                   | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-03b  | @GunaPalanivel         | `SECURITY_AUDIT_2026-04-25.md` with SC-N status     | #\_\_    | #\_\_ | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-03c  | @aravindsai003         | Demo machine pre-conditions checklist               | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-04   | @GunaPalanivel         | Submit hackathon form on WeMakeDevs                 | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-05   | @GunaPalanivel         | Link demo video + repo in submission                | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-06   | @5009226-bhawikakumari | Verify GFI PR status                                | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-07   | @GunaPalanivel         | Comment submission link on #26645 + #26608          | upstream | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |
| P4-08   | All                    | Team retrospective within 48h                       | #\_\_    | n/a   | [ ] | [ ] | [ ] | [ ] | [ ] | [ ]       | [ ] | [ ] |

---

## Snapshot per person (counts so far)

| Owner                  | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Total |
| ---------------------- | ------- | ------- | ------- | ------- | ------- | ----- |
| @GunaPalanivel         | 9       | 6       | 5       | 5       | 6       | 31    |
| @PriyankaSen0902       | 0       | 4       | 6       | 5       | 0       | 15    |
| @aravindsai003         | 0       | 5       | 5       | 4       | 1       | 15    |
| @5009226-bhawikakumari | 0       | 5       | 5       | 6       | 3       | 19    |

Update the counts above only if you add or remove rows.
