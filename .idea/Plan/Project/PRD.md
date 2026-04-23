# Product Requirements Document (PRD)

## Project: OpenMetadata MCP Agent

---

## Vision & Mission Alignment

> **OpenMetadata's tagline**: "Empower your Data Journey with OpenMetadata" ([README.md line 8](../../../README.md))
>
> **Collate's mission**: "Take the chaos out of the lives of data practitioners by providing a single pane view of all your data, and empowering collaboration." ([getcollate.io/about](https://www.getcollate.io/about))

This project advances both. The governance loop (scan → classify → confirm → apply → notify) is the chaos. Our agent collapses it to one chat sentence with a HITL safety gate. Every feature maps to a stated OM/Collate priority — see [VisionAlignment.md](./VisionAlignment.md) for the per-feature, per-component, per-value mapping.

## Judge Persona

The likely scoring panel ([JudgePersona.md](./JudgePersona.md)):

- **Suresh Srinivas** (CEO, Hadoop committer, ex-Hortonworks, ex-Uber Chief Architect) — cares about real-world data team usability, system thinking, "this would actually work in a Fortune 500"
- **Sriharsha Chintalapani** (CTO, Apache Kafka/Storm PMC, ex-Uber) — cares about clean code, layer separation, structured logging, ADRs, reproducible builds
- **@PubChimps** (track maintainer) — cares about respect for existing OM surface; will not assign issues
- **Bot reviewers** (gitar, Copilot, github-actions) — flag prompt injection, supply-chain hygiene, division-by-zero (already caught a competitor on PR [#27506](https://github.com/open-metadata/OpenMetadata/pull/27506))

Three demo moments designed for this panel are detailed in [JudgePersona.md](./JudgePersona.md) (Moment 1–3).

---

## Problem Statement

Data teams across enterprises manage thousands of tables, dashboards, and pipelines. OpenMetadata provides excellent metadata cataloging, but governance tasks remain manual:

1. **Manual classification** — Data stewards manually tag PII, sensitivity levels, and tiers across hundreds of assets
2. **No conversational interface** — Teams must navigate the UI or learn the REST API to query governance state
3. **Impact analysis is tedious** — Understanding "what breaks if I drop this table?" requires manual lineage traversal
4. **No cross-tool orchestration** — OpenMetadata data doesn't flow into GitHub Issues, Slack alerts, or compliance dashboards automatically

## Solution

A **standalone Python application** that acts as:

1. **Multi-MCP Agent Orchestrator** — Connects to OpenMetadata's MCP server + external MCP servers (GitHub, Slack)
2. **Conversational Governance Interface** — Chat UI for NL-driven data discovery and governance actions
3. **Automated Classification Engine** — LLM-powered entity scanning, tag suggestion, and batch application
4. **Lineage Impact Analyzer** — Human-readable impact analysis from lineage graph traversal

## Target Issues (GitHub)

| Issue                                                                | Title                                | Status                                                               |
| -------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------- |
| [#26645](https://github.com/open-metadata/OpenMetadata/issues/26645) | Multi-MCP Agent Orchestrator         | 🟡 Open — **NOT assigned** (per @PubChimps Apr 18); open competition |
| [#26608](https://github.com/open-metadata/OpenMetadata/issues/26608) | Conversational Data Catalog Chat App | 🟡 Open — **NOT assigned** (per @PubChimps Apr 18); open competition |

> ⚠️ **Active competing prototypes** (verified Apr 19, 2026):
>
> - **#26608**: @thisisvaishnav has a [Loom demo](https://www.loom.com/share/c2fc5f9fb9314c279faa1fc9967576f3) of a working chat UI with Claude + MCP tool chaining (`search_metadata`, `semantic_search`, `get_entity_details`, `get_entity_lineage`, `root_cause_analysis`). @asadjan4611 posted a phased orchestrator design. @ganeshark04, @krishB-Me, @farhanrhine, @xlordx-bit also building.
> - **#26645**: @0xSaksham confirmed LangGraph implementation in progress. @MonotonousHarsh, @afifasyed123, @KimtVak8143 also building.
>
> **Differentiation strategy**: Lead with **governance write-back + multi-MCP** (most prototypes are read-only chat). Our `patch_entity`-driven auto-classification + cross-MCP "OM → GitHub issue" workflow is the wedge.

## Non-Goals (v1)

- ❌ Modifying the existing Java `openmetadata-mcp` module
- ❌ Building new OM connectors or ingestion pipelines
- ❌ Production deployment with HA, DR, or multi-tenant support
- ❌ Building a custom LLM — we use OpenAI GPT-4o-mini (free credits)
- ❌ Replacing the OM UI — this is a complementary chat interface

---

## Upstream contribution vs hackathon deliverable

| Track                  | What ships                                                                                                       | Merge target                                                                                                                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hackathon / judges** | Full **openmetadata-mcp-agent** repo: FastAPI + LangGraph + UI + seed + CI                                       | `GunaPalanivel/openmetadata-mcp-agent` `main`                                                                                                                                            |
| **Upstream-ready**     | Small, reviewable contributions that match OpenMetadata org standards (Apache 2.0, tests, no drive-by refactors) | **`open-metadata/OpenMetadata`** (or other official OM repos) via **fork PR** — typically a **GFI** or doc fix per [DataFindings/GoodFirstIssues.md](../DataFindings/GoodFirstIssues.md) |

The conversational agent **does not** land as a single PR into the OpenMetadata **core** monolith. “Winning” upstream means: (1) hackathon repo demonstrates depth of OM integration; (2) at least one **credible** upstream PR shows the team can ship in the OM ecosystem the same way maintainers expect.

---

## ⚖️ Scoring Strategy — Optimized Against Exact Judging Criteria

### Criterion 1: Potential Impact (Weight: High)

> "How effectively does the project address a meaningful problem or unlock a valuable use case in the metadata and data management space?"

| What We Demonstrate (with measurable outcomes)                                                                               | Impact Signal                                               |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Classify 50 tables in <60s wall-clock at <$0.05 OpenAI spend; >85% LLM-tag agreement vs human spot-check on 5 sampled tables | Quantifiable: hours of manual work → minute, dollar-bounded |
| Lineage impact report in plain English: traverses ≤3 hops both directions; flags Tier1 assets at risk with explicit warnings | Prevents production outages from schema changes             |
| Governance health: tag coverage %, PII exposure %, unclassified entity count via `search_metadata` aggregations              | Quantifiable metadata quality improvement                   |
| Multi-MCP: OM PII finding → GitHub issue per data steward, with the steward's name pre-mentioned (Phase 3)                   | Cross-platform governance workflow                          |

**Demo hook (revised, measurable)**: _"OpenMetadata's mission is to take the chaos out of the data practitioner's life. Today most of that chaos is the governance loop. We turned that loop into one chat sentence — 50 tables tagged, with a confirmation gate, in under a minute, for under five cents."_

**Score target**: 9/10

---

### Criterion 2: Creativity & Innovation (Weight: High)

> "How unique is the idea? Does it push the boundaries of what's possible with metadata discovery, observability, or governance?"

| Innovation                          | Why It's Novel                                                                                                |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Multi-MCP orchestration**         | Issue #26645 — nobody else will build this. Connects OM + GitHub + Slack MCP servers in one agent.            |
| **LLM-powered auto-classification** | Not rule-based — uses GPT-4o-mini to understand column semantics and suggest PII tags with confidence scores. |
| **Lineage-to-English translation**  | Raw lineage graphs → human-readable impact reports with critical asset warnings.                              |
| **Governance-as-conversation**      | Not just "search metadata" — multi-step workflows: scan → classify → confirm → apply → report.                |

**What makes us unique vs. other chatbot submissions**: We don't just QUERY metadata. We GOVERN it. The agent takes action (patch_entity), not just answers questions.

**Score target**: 9/10

---

### Criterion 3: Technical Excellence (Weight: High)

> "How well is the project implemented? Does it demonstrate strong engineering practices and clean, maintainable code?"

| Practice           | Implementation                                           |
| ------------------ | -------------------------------------------------------- |
| **Architecture**   | LangGraph state machine, not a messy script              |
| **Type safety**    | Full Python type hints, Pydantic models                  |
| **Error handling** | Every MCP call wrapped with retry + graceful degradation |
| **Logging**        | Structured logging at INFO/DEBUG levels, no print()      |
| **Tests**          | Unit tests (mock MCP) + integration tests + E2E          |
| **Config**         | `.env` + `AISdkConfig.from_env()` — no hardcoded secrets |
| **Clean code**     | Small focused functions, docstrings, consistent naming   |
| **CI**             | pytest + ruff/black formatting in GitHub Actions         |

**Score target**: 8/10

---

### Criterion 4: Best Use of OpenMetadata (Weight: Critical)

> "How deeply and effectively does the project integrate with OpenMetadata's APIs, connectors, lineage, governance, or observability features?"

| OM Feature                                               | How We Use It                                                                                            |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **MCP Server** (all 12 tools)                            | Via official `data-ai-sdk` Python SDK — 7 via typed `MCPTool` enum, 5 by name via `client.mcp.call_tool` |
| **Search** (`search_metadata`)                           | NL query translation, governance scanning                                                                |
| **Semantic Search** (`semantic_search`)                  | Conceptual data discovery                                                                                |
| **Entity Details** (`get_entity_details`)                | Column inspection for classification                                                                     |
| **Patch Entity** (`patch_entity`)                        | Apply PII tags, tier labels                                                                              |
| **Lineage** (`get_entity_lineage`)                       | Impact analysis, dependency mapping                                                                      |
| **Root Cause Analysis** (`root_cause_analysis`)          | Data quality governance                                                                                  |
| **Glossary** (`create_glossary`, `create_glossary_term`) | Auto-generate governance glossary                                                                        |
| **Metrics** (`create_metric`)                            | Governance KPIs                                                                                          |
| **Test Cases** (`create_test_case`)                      | Data quality automation                                                                                  |
| **RBAC**                                                 | JWT auth, user-scoped permissions                                                                        |
| **Search Aggregations**                                  | Tag coverage %, PII exposure metrics                                                                     |

**We exercise all 12 MCP tools end-to-end** — 7 via the SDK's typed `MCPTool` enum (`SEARCH_METADATA`, `GET_ENTITY_DETAILS`, `GET_ENTITY_LINEAGE`, `CREATE_GLOSSARY`, `CREATE_GLOSSARY_TERM`, `CREATE_LINEAGE`, `PATCH_ENTITY`) plus 5 via `client.mcp.call_tool` by name (`semantic_search`, `get_test_definitions`, `create_test_case`, `create_metric`, `root_cause_analysis`). This is our strongest criterion.

**Score target**: 10/10

---

### Criterion 5: User Experience (Weight: Medium-High)

> "Is the project intuitive to use? Does it provide a seamless, polished experience that users would actually want to adopt?"

| UX Element               | Implementation                                                       |
| ------------------------ | -------------------------------------------------------------------- |
| **Chat interface**       | Familiar chat UI, type in natural language, get structured responses |
| **OM-native styling**    | Purple #7147E8, Inter font, dark mode — looks like an OM feature     |
| **Structured responses** | Tables for search results, tree view for lineage, badges for tags    |
| **Human-in-the-loop**    | "Found 12 PII columns. Apply tags? [Yes/No]" — no auto-actions       |
| **Error UX**             | "No PII detected in this schema" — clear, not cryptic                |
| **Loading states**       | Typing indicator, progress bar for batch classification              |
| **Help text**            | "Try: 'classify PII in customer_db' or 'what depends on orders?'"    |

**Score target**: 8/10

---

### Criterion 6: Presentation Quality (Weight: Medium)

> "How clearly is the project presented? Does the demo, README, and submission effectively communicate the problem, solution, and impact?"

| Element                  | Quality Bar                                                                               |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| **README.md**            | GIF at top, 1-liner, features list, architecture diagram (Mermaid), setup in 3 steps      |
| **Demo video**           | 2–3 min, narrated, shows all 4 workflows, failure handling, real data                     |
| **Architecture diagram** | Mermaid in README — system context, data flow, auth flow                                  |
| **AI Disclosure**        | "Built with OpenAI GPT-4o-mini via LangGraph + data-ai-sdk" (required by hackathon rules) |
| **Code comments**        | Docstrings on all public functions                                                        |
| **Setup UX**             | `git clone → pip install -e . → set .env → run` in <3 minutes                             |

**Score target**: 8/10

---

## Overall Score Projection

| Criterion                | Weight      | Our Target | Strategy                                  |
| ------------------------ | ----------- | ---------- | ----------------------------------------- |
| Potential Impact         | High        | 9/10       | Lead with governance workflow automation  |
| Creativity & Innovation  | High        | 9/10       | Multi-MCP is our #1 differentiator        |
| Technical Excellence     | High        | 8/10       | Clean architecture, tests, error handling |
| Best Use of OpenMetadata | Critical    | 10/10      | ALL 12 MCP tools via official SDK         |
| User Experience          | Medium-High | 8/10       | OM-native UI, human-in-the-loop           |
| Presentation Quality     | Medium      | 8/10       | Polished README, narrated demo            |

**Projected composite**: **52/60 (87%)** — top-tier submission territory.

---

## Confirmed Tech Stack

| Component       | Technology                                                                                            | Confirmed? |
| --------------- | ----------------------------------------------------------------------------------------------------- | ---------- |
| LLM             | OpenAI GPT-4o-mini (free credits)                                                                     | Yes        |
| Agent Framework | LangGraph + langchain-openai                                                                          | Yes        |
| MCP Client      | `data-ai-sdk[langchain]` for OM (Phases 1–2); `langchain-mcp-adapters` only for GitHub MCP in Phase 3 | Yes        |
| Backend         | FastAPI + Uvicorn                                                                                     | Yes        |
| Frontend        | React + Vite + TypeScript                                                                             | Yes        |
| Observability   | structlog (JSON) + prometheus-client                                                                  | Yes        |
| Resilience      | httpx + tenacity + pybreaker                                                                          | Yes        |
| Testing         | pytest + pytest-asyncio + respx + playwright (E2E)                                                    | Yes        |
| Lint/Type       | ruff + mypy --strict                                                                                  | Yes        |
| Security scan   | pip-audit + bandit + gitleaks                                                                         | Yes        |
| CI              | GitHub Actions (per [Security/CIHardening.md](../Security/CIHardening.md))                            | Yes        |
| Repo            | NEW standalone repo (separate from fork)                                                              | Yes        |
| OpenMetadata    | Docker instance (local)                                                                               | Yes        |

Full per-layer rationale + alternatives considered: [TechStackDR.md](./TechStackDR.md).

---

## Cross-references

| What you need                                                            | Where                                                                                                                                                                                    |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Discovery summary (V1 success metric, sensitive data, etc.)              | [Discovery.md](./Discovery.md)                                                                                                                                                           |
| Concrete NFR thresholds (timeouts, retries, rate limits, error envelope) | [NFRs.md](./NFRs.md)                                                                                                                                                                     |
| Architecture decisions and alternatives                                  | [Decisions.md](./Decisions.md)                                                                                                                                                           |
| System diagram + trust boundaries + observability subsystem              | [../Architecture/Overview.md](../Architecture/Overview.md)                                                                                                                               |
| Pydantic models + API contract                                           | [../Architecture/DataModel.md](../Architecture/DataModel.md), [../Architecture/APIContract.md](../Architecture/APIContract.md)                                                           |
| Coding standards (Three Laws of Implementation)                          | [../Architecture/CodingStandards.md](../Architecture/CodingStandards.md)                                                                                                                 |
| Threat model + Module-G prompt-injection defense                         | [../Security/ThreatModel.md](../Security/ThreatModel.md), [../Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md)                                           |
| Per-phase quality gates + PRR                                            | [../Validation/QualityGates.md](../Validation/QualityGates.md), [../Validation/PRR.md](../Validation/PRR.md)                                                                             |
| Risk register + runbook + competitive matrix + failure recovery          | [RiskRegister.md](./RiskRegister.md), [Runbook.md](./Runbook.md), [../Demo/CompetitiveMatrix.md](../Demo/CompetitiveMatrix.md), [../Demo/FailureRecovery.md](../Demo/FailureRecovery.md) |
