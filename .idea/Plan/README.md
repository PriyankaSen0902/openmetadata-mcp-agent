# OpenMetadata Hackathon — Plan Hub

## 🏆 WeMakeDevs × OpenMetadata Hackathon: "Back to the Metadata"

| Field               | Value                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------- |
| **Track**           | Paradox #T-01: MCP Ecosystem & AI Agents                                                     |
| **Project**         | OpenMetadata MCP Agent                                                                       |
| **Deadline**        | April 26, 2026                                                                               |
| **Hackathon Start** | April 17, 2026                                                                               |
| **Today**           | Day 3 (April 19) — **7 days remaining**                                                      |
| **Project Repo**    | `GunaPalanivel/openmetadata-mcp-agent` _(NEW — to be created)_                               |
| **Fork Repo**       | [GunaPalanivel/OpenMetadata](https://github.com/GunaPalanivel/OpenMetadata) _(GFI PRs only)_ |
| **Board**           | [GitHub Project Board](https://github.com/orgs/open-metadata/projects/107/views/1)           |
| **Rules**           | [WeMakeDevs Hackathon Page](https://www.wemakedevs.org/hackathons/openmetadata)              |
| **LLM**             | OpenAI GPT-4o-mini (free Codex Hackathon credits)                                            |
| **Start Status**    | 🆕 Fresh start — no prior code from any team member                                          |

---

## 👥 Team — "The Mavericks"

| ID       | Name           | GitHub                                                             | Role                  | Primary Area                                                             |
| -------- | -------------- | ------------------------------------------------------------------ | --------------------- | ------------------------------------------------------------------------ |
| OMH-GSA  | Guna Palanivel | [@GunaPalanivel](https://github.com/GunaPalanivel)                 | Architect / Tech Lead | Agent orchestrator, MCP client, governance engine, PR review, submission |
| OMH-PSTL | Priyanka Sen   | [@PriyankaSen0902](https://github.com/PriyankaSen0902)             | Senior Builder        | MCP client SDK, tool-calling, API integration, governance flows          |
| OMH-ATL  | Aravind Sai    | [@aravindsai003](https://github.com/aravindsai003)                 | Builder / Validator   | Chat UI, Docker OM setup, integration testing, validation                |
| OMH-BSE  | Bhawika Kumari | [@5009226-bhawikakumari](https://github.com/5009226-bhawikakumari) | Delivery / Docs       | README, demo video, GFI PR, documentation, demo prep                     |

---

## ⚖️ Judging Criteria (Direct from Hackathon)

| #   | Criterion                | Our Target | Key Strategy                                                                                                                                                                                    |
| --- | ------------------------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 01  | Potential Impact         | 9/10       | Auto-classify 50+ tables; lineage impact before schema changes                                                                                                                                  |
| 02  | Creativity & Innovation  | 9/10       | Multi-MCP orchestration; LLM classification (not rules)                                                                                                                                         |
| 03  | Technical Excellence     | 8/10       | LangGraph architecture, tests, CI, structured logging                                                                                                                                           |
| 04  | Best Use of OpenMetadata | 10/10      | All 12 MCP tools — 7 via typed `MCPTool` enum, 5 (`semantic_search`, `get_test_definitions`, `create_test_case`, `create_metric`, `root_cause_analysis`) via `client.mcp.call_tool(name, args)` |
| 05  | User Experience          | 8/10       | OM-native chat UI, human-in-the-loop, structured responses                                                                                                                                      |
| 06  | Presentation Quality     | 8/10       | GIF README, 2-min demo, Mermaid diagrams                                                                                                                                                        |

---

## 🎯 Vision & Mission Alignment

> "Empower your Data Journey with OpenMetadata" — [OpenMetadata `README.md` line 8](../../README.md)
>
> "Take the chaos out of the lives of data practitioners by providing a single pane view of all your data, and empowering collaboration." — [Collate, getcollate.io/about](https://www.getcollate.io/about)

This project advances both. See [Project/VisionAlignment.md](./Project/VisionAlignment.md) for the per-feature mapping and [Project/JudgePersona.md](./Project/JudgePersona.md) for the judge profile (Suresh Srinivas, Sriharsha Chintalapani — distributed-systems veterans).

## 📁 Folder Map

```
.idea/Plan/ (published — engineering plan hub; committed via !.idea/Plan/ in .gitignore)
├── README.md                      ← THIS FILE
├── TaskSync.md                    ← Master task list (ordered, per-person)
├── Project/                       ← PRD, ADRs, Discovery, NFRs, Vision, Judges, Risks, Runbook, TechStack
├── Architecture/                  ← System design, Data Model, API Contract, CLAUDE template, Coding Standards
├── Security/                      ← Threat Model, Prompt Injection, Control Coverage, Secrets, CI Hardening
├── DataFindings/                  ← MCP audit, board status, API analysis, GFI
├── FeatureDev/                    ← Per-feature specs (+ [GovernanceEngine.md](./FeatureDev/GovernanceEngine.md))
├── Validation/                    ← Setup guide, Test Strategy, Quality Gates, PRR
├── PR-Review/                     ← PR workflow, review log
├── Demo/                          ← Narrative, Submission Checklist, Competitive Matrix, Failure Recovery
└── IssueAnalyzer/                 ← Hackathon board tracking
```

---

## 🔄 Lifecycle (Every Feature)

```
PLAN → BUILD → VALIDATE → FIX → VALIDATE → PR DRAFT → REVIEWER → MERGE
```

- No self-merges. All PRs go through review.
- Reviewer routing is automatic via `.github/workflows/auto-assign-reviewer.yml`:
  - PR opened by a team member (@PriyankaSen0902, @aravindsai003, @5009226-bhawikakumari) → @GunaPalanivel is requested
  - PR opened by anyone outside the team (forks / community) → @PriyankaSen0902 is requested
  - PR opened by @GunaPalanivel → @PriyankaSen0902 is requested
- All PRs use `PR-Review/PRTemplate.md`
- Review against `PR-Review/Checklist.md`
- **16 engineering issues** use [PR-Review/EngineeringIssueTemplate.md](./PR-Review/EngineeringIssueTemplate.md) for GitHub issue bodies ([TaskSync.md §Sixteen-issue](./TaskSync.md))
- Track per-person, per-phase progress in [Progress.md](./Progress.md)

---

## 🔗 Quick Links

### Core

- [TaskSync.md](./TaskSync.md) — What to do next (Phase 0 → 4)
- [Progress.md](./Progress.md) — Per-person, per-phase progress tracker (issue → PR → merge)
- [Project/PRD.md](./Project/PRD.md) — Judging-aligned requirements
- [Project/Discovery.md](./Project/Discovery.md) — Phase 1 Discovery Summary (V1 Success Metric, Sensitive Data, etc.)
- [Project/NFRs.md](./Project/NFRs.md) — NFRs + The 5 Things AI Never Adds (concrete numbers)
- [Project/Milestones.md](./Project/Milestones.md) — Phase timeline
- [Project/Decisions.md](./Project/Decisions.md) — ADRs

### Vision & Judges

- [Project/VisionAlignment.md](./Project/VisionAlignment.md) — Collate mission + OM tagline mapping
- [Project/JudgePersona.md](./Project/JudgePersona.md) — Suresh + Sriharsha profile + 3 demo moments
- [Project/RiskRegister.md](./Project/RiskRegister.md) — Top 10 demo-killing risks + mitigations
- [Project/Runbook.md](./Project/Runbook.md) — Demo-day operations + 8 failure modes
- [Project/TechStackDR.md](./Project/TechStackDR.md) — Consolidated Tech Stack Decision Record

### Feature specs

- [FeatureDev/GovernanceEngine.md](./FeatureDev/GovernanceEngine.md) — Governance FSM, HITL confirm, OM write-back, drift, similarity, 16-issue map

### PR workflow

- [PR-Review/EngineeringIssueTemplate.md](./PR-Review/EngineeringIssueTemplate.md) — Mandatory GitHub issue template (Context → Acceptance criteria)
- [PR-Review/Checklist.md](./PR-Review/Checklist.md) — Review checklist
- [PR-Review/PRTemplate.md](./PR-Review/PRTemplate.md) — PR template

### Architecture

- [Architecture/Overview.md](./Architecture/Overview.md) — System context + Trust Boundary diagram + Observability subsystem
- [Architecture/DataModel.md](./Architecture/DataModel.md) — Pydantic shapes (ChatSession, PendingSession, ToolCallProposal, governance models, error envelope)
- [Architecture/APIContract.md](./Architecture/APIContract.md) — Full FastAPI contract (`/chat`, `/chat/confirm`, `/healthz`, `/metrics`)
- [Architecture/CLAUDETemplate.md](./Architecture/CLAUDETemplate.md) — `CLAUDE.md` to drop into the new repo root
- [Architecture/CodingStandards.md](./Architecture/CodingStandards.md) — The Three Laws of Implementation in Python

### Security

- [Security/ThreatModel.md](./Security/ThreatModel.md) — SC-N claims, ENTRY-N entrypoints, Sensitive Sinks, Trust Boundary
- [Security/PromptInjectionMitigation.md](./Security/PromptInjectionMitigation.md) — Module G five-layer defense
- [Security/ControlCoverage.md](./Security/ControlCoverage.md) — 9-area Control Coverage Matrix
- [Security/SecretsHandling.md](./Security/SecretsHandling.md) — `AI_SDK_TOKEN` + `OPENAI_API_KEY` + `GITHUB_TOKEN` policy
- [Security/CIHardening.md](./Security/CIHardening.md) — GitHub Actions permissions, SHA-pinning, dependabot

### Validation

- [Validation/QualityGates.md](./Validation/QualityGates.md) — Per-phase Architecture / Resilience / Observability / Security / AI-ML gates
- [Validation/PRR.md](./Validation/PRR.md) — Hackathon-scoped Production Readiness Review
- [Validation/TestStrategy.md](./Validation/TestStrategy.md) — Test pyramid + acceptance criteria
- [Validation/SetupGuide.md](./Validation/SetupGuide.md) — Local bring-up

### Demo

- [Demo/Narrative.md](./Demo/Narrative.md) — Demo script
- [Demo/CompetitiveMatrix.md](./Demo/CompetitiveMatrix.md) — Feature-by-feature vs all named competitors
- [Demo/FailureRecovery.md](./Demo/FailureRecovery.md) — Backup recording, frozen seed dataset, recovery procedure
- [Demo/SubmissionChecklist.md](./Demo/SubmissionChecklist.md) — Final submission gate

### Data Findings

- [DataFindings/ExistingMCPAudit.md](./DataFindings/ExistingMCPAudit.md) — 12 existing tools + AI SDK coverage
- [DataFindings/BoardStatus.md](./DataFindings/BoardStatus.md) — Hackathon board + active competitors
- [DataFindings/GoodFirstIssues.md](./DataFindings/GoodFirstIssues.md) — GFI status + Slack outreach plan

---

## ✅ Verified Against (April 19, 2026)

| Claim                                             | Source                                                                                                                                                            |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 12 MCP tools in OM MCP server                     | [`openmetadata-mcp/src/main/resources/json/data/mcp/tools.json`](../../openmetadata-mcp/src/main/resources/json/data/mcp/tools.json) (12 entries)                 |
| `data-ai-sdk` is the official Python SDK          | [PyPI v0.1.2](https://pypi.org/project/data-ai-sdk/) + [docs.open-metadata.org/v1.12.x/sdk/ai-sdk](https://docs.open-metadata.org/v1.12.x/sdk/ai-sdk)             |
| SDK exposes 7 typed `MCPTool` enum members        | [`open-metadata/ai-sdk` `python/src/ai_sdk/mcp/models.py`](https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/models.py) — `MCPTool` StrEnum |
| MCP transport: HTTP POST `/mcp` JSON-RPC 2.0      | [`openmetadata-mcp/README.md`](../../openmetadata-mcp/README.md) + AI SDK `docs/mcp.md`                                                                           |
| Hackathon dates, prizes, $100/PR, max team 4      | [wemakedevs.org/hackathons/openmetadata](https://www.wemakedevs.org/hackathons/openmetadata)                                                                      |
| #26645, #26608, #26646, #26609 NOT being assigned | @PubChimps comments dated Apr 18, 2026 on each issue                                                                                                              |
| Project Board #107 (T-01..T-06 paradoxes)         | [github.com/orgs/open-metadata/projects/107/views/1](https://github.com/orgs/open-metadata/projects/107/views/1)                                                  |
