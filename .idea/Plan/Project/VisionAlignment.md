# Vision & Mission Alignment

> A first-prize submission demonstrably advances the host project's stated mission. This doc maps OpenMetadata MCP Agent to OpenMetadata's published vision, Collate's mission, OM's four core components, and Collate's six core values.

## OpenMetadata's stated tagline

> **"Empower your Data Journey with OpenMetadata"** — [OpenMetadata `README.md` line 8](../../../README.md)

OpenMetadata describes itself as a "unified metadata platform for data discovery, data observability, and data governance powered by a central metadata repository, in-depth column-level lineage, and seamless team collaboration."

## Collate's mission (the company behind OpenMetadata)

> **"We are on a mission to take the chaos out of the lives of data practitioners by providing a single pane view of all your data, and empowering collaboration."** — [getcollate.io/about](https://www.getcollate.io/about)

## How our project advances each line

| OpenMetadata / Collate goal                             | OpenMetadata MCP Agent feature                                                                                                                 | Evidence in code (planned)                                                                                                       |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| "Take the chaos out of the lives of data practitioners" | Replace the manual scan→tag→confirm→apply governance loop with one chat sentence                                                               | [FeatureDev/AutoClassification.md](../FeatureDev/AutoClassification.md) — `auto-classify PII in customer_db`                     |
| "Single pane view of all your data"                     | Conversational interface to the entire 12-tool MCP surface — search, semantic search, lineage, RCA, glossary, metrics, tests — from one prompt | [Architecture/Overview.md](../Architecture/Overview.md), [DataFindings/ExistingMCPAudit.md](../DataFindings/ExistingMCPAudit.md) |
| "Empowering collaboration"                              | Multi-MCP cross-platform: OM → GitHub issue per data steward, with the steward's name pre-mentioned                                            | [FeatureDev/MultiMCPOrchestrator.md](../FeatureDev/MultiMCPOrchestrator.md)                                                      |
| "Empower your Data Journey"                             | NL queries replace OpenSearch DSL knowledge; lineage graphs translated to plain-English impact reports for non-engineers                       | [FeatureDev/LineageImpact.md](../FeatureDev/LineageImpact.md), [FeatureDev/NLQueryEngine.md](../FeatureDev/NLQueryEngine.md)     |

## Mapping to OpenMetadata's four components

OpenMetadata is built on four pillars per [`README.md` line 33-37](../../../README.md). We exercise three directly and respect the fourth.

| OM Component            | What it is                                    | How our agent uses it                                                                                                                                                                                                 |
| ----------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Metadata Schemas**    | Core JSON-Schema definitions for every entity | Our LLM prompts include the FQN format and the entity-type vocabulary from [`openmetadata-spec/.../mcpToolDefinition.json`](../../../openmetadata-spec/src/main/resources/json/schema/api/mcp/mcpToolDefinition.json) |
| **Metadata Store**      | The MySQL + Elasticsearch backbone            | Read via `search_metadata` / `semantic_search`; write via `patch_entity` / `create_glossary*` / `create_lineage` — every call routed through MCP, never direct to MySQL                                               |
| **Metadata APIs**       | REST + MCP surface                            | We are a 100% API-first consumer — the `data-ai-sdk` MCP client is the single ingress; the Java MCP server is unmodified                                                                                              |
| **Ingestion Framework** | 84+ connectors                                | Out of scope for v1 — we consume the metadata that ingestion produced; we do not build a new connector                                                                                                                |

## Mapping to Collate's six core values

> Per [getcollate.io/about](https://www.getcollate.io/about). Each value is something Collate's team uses to evaluate work. We use them to self-assess our submission.

| Collate value            | What it means at Collate                          | How our submission demonstrates it                                                                                                                                                                                   |
| ------------------------ | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Grow Together**        | Collaboration to learn together                   | OSS Apache 2.0; reproducible seed data; CLAUDE.md so future contributors inherit the architectural contract; every ADR explains the reasoning                                                                        |
| **Align with Customers** | Empathic listening to user needs                  | Our V1 Success Metric ([Discovery.md](./Discovery.md)) is framed from the data steward's perspective: "scan + tag 50 tables in <60s with 1 confirmation click" — not a tech metric                                   |
| **Act Fast**             | Keep in sync with rapidly evolving data ecosystem | Built in 7 days; uses `data-ai-sdk` v0.1.2 (released Mar 2026, the latest); LangGraph (latest stable); MCP JSON-RPC 2.0 (current spec)                                                                               |
| **Be Proactive**         | Think ahead; attention to detail                  | We document risks ([RiskRegister.md](./RiskRegister.md)) before they happen; we ship a runbook ([Runbook.md](./Runbook.md)) and a [FailureRecovery.md](../Demo/FailureRecovery.md) for the demo before recording it  |
| **Deliver Value**        | Address unmet needs of the data community         | The governance write-back loop (`scan → classify → confirm → patch_entity`) does not exist in the current OM UI or any competitor's hackathon submission ([Demo/CompetitiveMatrix.md](../Demo/CompetitiveMatrix.md)) |
| **Love Challenges**      | Driven to tackle complex problems                 | Cross-MCP orchestration (OM + GitHub) + LLM-driven classification + prompt-injection defense for catalog content + human-in-the-loop write gating — none of these are off-the-shelf                                  |

## Mapping to the six judging criteria

> From the [hackathon page](https://www.wemakedevs.org/hackathons/openmetadata). Cross-referenced with our scoring strategy in [PRD.md](./PRD.md).

| Criterion                | Vision linkage         | Our differentiator                                                                                                             |
| ------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Potential Impact         | "Take the chaos out"   | Quantified: 50 tables tagged in <60s vs hours of manual work; multi-MCP unblocks team-wide governance flow                     |
| Creativity & Innovation  | "Love Challenges"      | Cross-MCP + governance write-back + Module-G prompt-injection defense (no other competitor mitigates this)                     |
| Technical Excellence     | "Be Proactive"         | All 5 production controls explicitly specified in [NFRs.md](./NFRs.md) BEFORE any code is written                              |
| Best Use of OpenMetadata | "Single pane view"     | All 12 MCP tools exercised; uses official `data-ai-sdk`; no upstream code modifications                                        |
| User Experience          | "Align with Customers" | Chat metaphor familiar; OM-native styling (`#7147E8`, Inter font); HITL confirmation prevents footgun writes                   |
| Presentation Quality     | "Grow Together"        | Mermaid architecture + trust boundary diagrams; ADRs explain every choice; Runbook + FailureRecovery show operational maturity |

## What this means for the demo

The demo opening line should reference the mission:

> "OpenMetadata's mission is to take the chaos out of the data practitioner's life. Today most of that chaos is the _governance loop_ — scan, classify, confirm, apply, notify. We turned that loop into one sentence in chat."

This is the line in [Demo/Narrative.md](../Demo/Narrative.md) we should rehearse first.
