# MCP Tool → Governance Use-Case Mapping

> **Issue**: [#21 — P1-08](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/21)
> **Depends on**: [#20 — P1-07](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/20) (tool schema audit)
> **Unblocks**: [#22 — P1-09](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/22) (typed Pydantic wrappers — prioritized by this mapping)
> **Author**: @PriyankaSen0902
> **Date**: April 20, 2026

---

## Purpose

This document maps each of the 12 OpenMetadata MCP tools to a **concrete governance use case**, tied to the PRD acceptance criteria. This mapping drives:

1. Which tools get typed wrappers first (issue #22)
2. Which tools appear in the demo
3. The agent's governance workflow design

---

## Master Mapping Table

| # | Tool Name | Governance Use Case | Governance Category | PRD Criterion | Demo Priority | Wrapper Priority |
|---|-----------|-------------------|-------------------|--------------|--------------|-----------------|
| 1 | `search_metadata` | Find all untagged tables in a schema to compute tag-coverage % and identify governance gaps | Classification & Compliance Scanning | C4 — Best Use of OM (search aggregations for tag coverage %) | 🔴 Critical | P0 — Core |
| 2 | `semantic_search` | Discover tables related to "customer spending" or "personal data" for PII audit without knowing exact names | PII Discovery & Data Subject Identification | C1 — Potential Impact (classify 50 tables), C2 — Creativity (LLM classification) | 🟠 High | P0 — Core |
| 3 | `get_entity_details` | Inspect a table's columns, existing tags, and description before LLM classifies it for PII | Pre-Classification Inspection | C4 — Best Use of OM (column inspection), C3 — Technical Excellence (type safety) | 🔴 Critical | P0 — Core |
| 4 | `patch_entity` | Apply PII tag to a column after LLM classification confirms it; update description with governance notes | Tag Application & Metadata Enrichment | C1 — Potential Impact (auto-classify 50 tables), C4 — Best Use of OM (patch_entity write-back) | 🔴 Critical | P0 — Core |
| 5 | `get_entity_lineage` | Trace upstream sources and downstream consumers before a schema change to generate a human-readable impact report | Impact Analysis & Change Management | C1 — Potential Impact (lineage impact before schema changes), C2 — Creativity (lineage-to-English) | 🔴 Critical | P0 — Core |
| 6 | `create_lineage` | Register a new data pipeline's lineage edge so governance policies propagate to its outputs automatically | Lineage Registration | C4 — Best Use of OM (all 12 tools) | 🟡 Medium | P2 — Phase 3 |
| 7 | `create_glossary` | Auto-generate a "Data Governance" glossary to house PII, sensitivity, and compliance terms discovered by the agent | Governance Vocabulary Management | C4 — Best Use of OM (glossary creation), C2 — Creativity (auto-generated governance glossary) | 🟡 Medium | P1 — Phase 2 |
| 8 | `create_glossary_term` | Create glossary terms like "PII — Personally Identifiable Information" with definitions linked to discovered entities | Governance Term Cataloging | C4 — Best Use of OM (glossary terms), C2 — Creativity | 🟡 Medium | P1 — Phase 2 |
| 9 | `get_test_definitions` | List available data quality tests (e.g., columnValuesToBeNotNull) to recommend appropriate DQ checks for a table | DQ Test Discovery | C4 — Best Use of OM (test definitions) | 🟢 Low | P2 — Phase 3 |
| 10 | `create_test_case` | Add a "columnValuesToBeNotNull" test on PII columns to ensure sensitive data is never null (compliance requirement) | DQ Governance Automation | C4 — Best Use of OM (test case creation) | 🟢 Low | P2 — Phase 3 |
| 11 | `root_cause_analysis` | When a downstream dashboard breaks, trace upstream to find which pipeline's data quality failure caused it | Root Cause & Incident Response | C1 — Potential Impact (prevent production outages), C4 — Best Use of OM (RCA) | 🟠 High | P1 — Phase 2 |
| 12 | `create_metric` | Create a "TagCoveragePercent" KPI metric tracking governance health over time | Governance KPI Tracking | C4 — Best Use of OM (metrics), C1 — Potential Impact (governance health) | 🟢 Low | P2 — Phase 3 |

---

## Governance Workflow Chains

These are multi-tool workflows our agent orchestrates:

### Chain 1: Auto-Classification (Demo Critical Path)

```
search_metadata → get_entity_details → [LLM classifies] → patch_entity
```

**Scenario**: "Classify all untagged tables in the finance schema for PII"

1. `search_metadata` — Find untagged tables via aggregation query (`must_not exists tags.tagFQN`)
2. `get_entity_details` — For each table, fetch column names, types, descriptions
3. **LLM** — GPT-4o-mini analyzes columns and suggests PII tags with confidence scores
4. `patch_entity` — Apply approved tags (after HITL confirmation gate)

**PRD tie-in**: C1 (classify 50 tables in <60s), C4 (all 12 tools), C5 (human-in-the-loop)

### Chain 2: Lineage Impact Analysis

```
get_entity_lineage → [LLM translates] → search_metadata (Tier1 check)
```

**Scenario**: "What breaks if I drop the orders table?"

1. `get_entity_lineage` — Traverse 3 hops upstream + downstream
2. **LLM** — Translate raw lineage graph to human-readable impact report
3. `search_metadata` — Check if any impacted entities are Tier1 (critical assets)

**PRD tie-in**: C1 (lineage impact report in plain English), C2 (lineage-to-English translation)

### Chain 3: Root Cause Governance

```
root_cause_analysis → get_entity_details → [LLM explains]
```

**Scenario**: "The sales dashboard data looks wrong — what happened?"

1. `root_cause_analysis` — Find upstream failures and downstream impact
2. `get_entity_details` — Inspect failed upstream entities for details
3. **LLM** — Generate human-readable root cause report with remediation steps

**PRD tie-in**: C1 (prevent production outages), C4 (root_cause_analysis tool)

### Chain 4: Governance Health Dashboard

```
search_metadata (aggregations) → create_metric → [LLM summarizes]
```

**Scenario**: "What's our overall governance health?"

1. `search_metadata` — Query with `includeAggregations: true` for tag coverage, PII exposure
2. `create_metric` — Register "TagCoveragePercent" and "PIIExposureCount" as trackable KPIs
3. **LLM** — Summarize governance posture in plain English

**PRD tie-in**: C1 (governance health: tag coverage %, PII exposure %), C4 (create_metric)

### Chain 5: Multi-MCP Cross-Platform (Phase 3)

```
search_metadata → patch_entity → [GitHub MCP: create_issue]
```

**Scenario**: "Found unresolved PII in production — alert the data steward"

1. `search_metadata` — Find PII-tagged entities without a data steward
2. `patch_entity` — Add interim governance tags
3. **GitHub MCP** — Create a GitHub issue assigned to the responsible team

**PRD tie-in**: C2 (multi-MCP orchestration), C1 (OM PII finding → GitHub issue)

---

## Wrapper Prioritization Summary

Based on governance use-case criticality and demo requirements:

| Priority | Tools | Rationale |
|----------|-------|-----------|
| **P0 — Core (Phase 1)** | `search_metadata`, `semantic_search`, `get_entity_details`, `patch_entity`, `get_entity_lineage` | Required for auto-classification + impact analysis demo chains |
| **P1 — Phase 2** | `create_glossary`, `create_glossary_term`, `root_cause_analysis` | Governance vocabulary + RCA workflows |
| **P2 — Phase 3** | `create_lineage`, `get_test_definitions`, `create_test_case`, `create_metric` | DQ automation + KPI tracking; lower demo priority |

---

## PRD Acceptance Criteria Cross-Reference

| PRD Criterion | Tools That Serve It | Coverage |
|--------------|-------------------|----------|
| C1: Potential Impact — classify 50 tables in <60s | `search_metadata`, `get_entity_details`, `patch_entity` | ✅ Full |
| C1: Potential Impact — lineage impact in plain English | `get_entity_lineage` | ✅ Full |
| C1: Potential Impact — governance health metrics | `search_metadata` (aggregations), `create_metric` | ✅ Full |
| C1: Potential Impact — OM → GitHub issue | `search_metadata`, `patch_entity` + GitHub MCP | ✅ Full |
| C2: Creativity — multi-MCP orchestration | All OM tools + GitHub MCP + Slack MCP | ✅ Full |
| C2: Creativity — LLM-powered classification | `get_entity_details` → LLM → `patch_entity` | ✅ Full |
| C2: Creativity — lineage-to-English | `get_entity_lineage` → LLM | ✅ Full |
| C3: Technical Excellence — type safety | All 11 typed `MCPTool` enum tools + 1 custom wrapper | ✅ Full |
| C4: Best Use of OM — all 12 MCP tools | All 12 tools mapped with governance use cases | ✅ Full |
| C5: User Experience — HITL confirmation | `patch_entity` gated by user approval | ✅ Full |
