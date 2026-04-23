# Milestones & Timeline

## Overview

| Phase                      | Dates     | Days | Focus                                         | Exit Criteria                                       |
| -------------------------- | --------- | ---- | --------------------------------------------- | --------------------------------------------------- |
| **Phase 0: Claim**         | Apr 19    | 0.5  | Claim issues, create repo, redeem API credits | Issues commented, repo created                      |
| **Phase 1: Foundation**    | Apr 19–20 | 1.5  | Scaffold, MCP client, first tool call         | `search_metadata` returns results via Python client |
| **Phase 2: Core Features** | Apr 21–23 | 3    | 3 governance workflows end-to-end             | NL query, auto-classify, lineage impact all work    |
| **Phase 3: Polish**        | Apr 24–25 | 2    | Multi-MCP, UI polish, error handling          | Demo recorded, all tests green                      |
| **Phase 4: Submit**        | Apr 26    | 1    | README finalization, submission               | Form submitted, repo clean                          |

## Execution waves (16 engineering issues)

Tightened execution for the final sprint: drive by **16 GitHub engineering issues** (see [TaskSync.md §Sixteen-issue engineering program](../TaskSync.md) and [FeatureDev/GovernanceEngine.md](../FeatureDev/GovernanceEngine.md)). Documentation and submission tasks stay in Phase 3–4 and **do not** consume one of the sixteen slots.

| Wave   | Target                  | Engineering issues (titles from GovernanceEngine table)                   |
| ------ | ----------------------- | ------------------------------------------------------------------------- |
| **W1** | HITL + governance core  | #1–#5 (sessions, FSM, hooks + write-back, drift service + API)            |
| **W2** | Product + UI            | #6–#11 (workflows, FE, OM-native)                                         |
| **W3** | Proof + differentiation | #12–#16 (Multi-MCP, test/security/coverage, CI, demo automation, **E2E**) |

---

## Phase 1 — Foundation (April 19–20)

**Goal**: Project scaffolded. MCP client connects to OM. First tool call works.

### Deliverables

1. Project initialized with `pyproject.toml`
2. Docker OM instance running locally at `:8585`
3. Python MCP client connects and calls `search_metadata`
4. LangGraph agent skeleton accepts NL input
5. React chat UI scaffold running locally
6. Plan/ folder committed with all stubs

### Owner Map

| Deliverable             | Owner              | Depends On |
| ----------------------- | ------------------ | ---------- |
| Project scaffold        | OMH-GSA            | —          |
| Docker OM setup         | OMH-ATL            | —          |
| MCP client + first call | OMH-GSA + OMH-PSTL | Docker OM  |
| Agent skeleton          | OMH-GSA            | MCP client |
| Chat UI scaffold        | OMH-ATL            | —          |
| Plan/ folder            | OMH-BSE            | —          |

### Exit Gate

- [ ] `python -m copilot search "show me tables"` returns results
- [x] Chat UI runs on `localhost:3000` (Vite; verification steps in [`ui/README.md`](../../ui/README.md); PR [\#73](https://github.com/GunaPalanivel/openmetadata-mcp-agent/pull/73))
- [ ] All Plan/ files committed

---

## Phase 2 — Core Features (April 21–23)

**Goal**: 3 governance workflows working end-to-end.

### Feature 1: NL Metadata Query

- User types natural language → Agent selects `search_metadata` or `semantic_search` → Returns structured results
- Owner: OMH-PSTL (implementation) + OMH-GSA (agent logic)

### Feature 2: Auto-Classification

- Agent scans entities → LLM classifies column names/descriptions for PII → Suggests tags → User approves → `patch_entity` applies
- Owner: OMH-GSA

### Feature 3: Lineage Impact Analysis

- User provides table FQN → Agent calls `get_entity_lineage` → Returns human-readable upstream/downstream impact report
- Owner: OMH-GSA

### Feature 4: Governance Summary (stretch within Phase 2)

- Agent scans catalog → Reports tag coverage %, PII exposure, unclassified assets
- Owner: OMH-PSTL

### Exit Gate

- [ ] All 3 core workflows testable from chat UI
- [ ] Unit tests passing for agent + MCP client
- [ ] API endpoint `POST /chat` working

---

## Phase 3 — Polish + Multi-MCP (April 24–25)

**Goal**: Demo recorded. All tests green. Multi-MCP working.

### Deliverables

1. Multi-MCP: connect 1 external MCP server (GitHub or Slack)
2. Cross-MCP workflow: "find PII tables → auto-create GitHub issue"
3. UI polish: OM-native styling, responsive
4. Error handling for all edge cases
5. Demo video recorded (2–3 min)
6. README finalized with architecture diagram

### Exit Gate

- [ ] Demo video covers all features
- [ ] README clone → run in <5 min
- [ ] All tests green
- [ ] No secrets or debug code in repo

---

## Phase 4 — Submit (April 26)

### Checklist

- [ ] Hackathon form submitted
- [ ] Repo public and clean
- [ ] GFI PR status confirmed
- [ ] Team retrospective completed
