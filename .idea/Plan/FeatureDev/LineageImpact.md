# Lineage Impact Analysis Feature Spec

## Owner: OMH-GSA (Guna)
## Phase: 2 (Day 5–7)

---

## Overview

Given a table FQN, traverse the lineage graph and produce a human-readable impact report showing upstream dependencies and downstream consumers.

## User Flow

```
User: "What breaks if I drop the customers table?"
→ Agent calls get_entity_lineage(fqn="service.db.schema.customers", downstreamDepth=5)
→ LLM translates raw lineage graph into human-readable impact report
→ Response:
  "⚠️ Dropping 'customers' affects 8 downstream assets:
   - 3 dashboards (customer_360, revenue_summary, churn_report)
   - 2 pipelines (daily_customer_etl, weekly_report_gen)
   - 3 tables (customer_metrics, customer_segments, customer_ltv)

   Critical impact: customer_360 dashboard is Tier 1 and owned by the exec team."

User: "Show me the upstream of the revenue_dashboard"
→ Agent calls get_entity_lineage(fqn="...", upstreamDepth=5)
→ Response:
  "revenue_dashboard depends on 4 upstream tables:
   1. orders (BigQuery) → direct
   2. products (BigQuery) → direct
   3. customers (BigQuery) → via orders
   4. pricing_rules (Snowflake) → via products

   ⚠️ Cross-service dependency: pricing_rules is in Snowflake while others are in BigQuery."
```

## MCP Tools Used

| Step | Tool | Params |
|------|------|--------|
| Get lineage | `get_entity_lineage` | `entityType`, `fqn`, `upstreamDepth`, `downstreamDepth` |
| Get entity details | `get_entity_details` | For each node: get tier, owners, tags |
| Root cause | `root_cause_analysis` | If user asks "why is this broken?" |

## LLM Prompt Template

```
You are a data lineage analyst. Given a lineage graph (nodes and edges), produce a human-readable impact report.

Entity: {entity_fqn}
Direction: {upstream|downstream}
Lineage Graph:
{lineage_json}

Rules:
1. List affected assets grouped by type (tables, dashboards, pipelines)
2. Highlight Tier 1 assets and cross-service dependencies
3. Note any data quality test failures on downstream assets
4. Be concise — no more than 10 lines
```

## Error Handling

- Entity not found → "Could not find entity with FQN: ..."
- No lineage → "This entity has no recorded lineage."
- Deep graph (>50 nodes) → truncate at 20, note "50+ assets affected"
