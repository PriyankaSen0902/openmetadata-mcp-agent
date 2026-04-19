# Auto-Classification Feature Spec

## Owner: OMH-GSA (Guna)
## Phase: 2 (Day 5–7)

---

## Overview

Scan entities in the OpenMetadata catalog, use an LLM to classify columns for PII/sensitivity, suggest tags, and apply them via `patch_entity`.

## User Flow

```
User: "Auto-classify PII in all tables in the customer_db"
→ Agent calls search_metadata(query="*", entityType="table", queryFilter=service:customer_db)
→ For each table: get_entity_details(fqn) → extract column names + descriptions
→ LLM classifies each column: {column_name, description} → PII category
→ Agent presents: "Found 12 PII columns across 5 tables. Apply tags?"
→ User confirms
→ Agent calls patch_entity for each table with PII tags
→ "Done. Tagged 12 columns as PII.Sensitive across 5 tables."
```

## MCP Tools Used

| Step | Tool | Params |
|------|------|--------|
| Scan | `search_metadata` | `entityType: "table"`, `queryFilter: service-specific` |
| Inspect | `get_entity_details` | `entityType: "table"`, `fqn: <table_fqn>` |
| Tag | `patch_entity` | `entityType: "table"`, `fqn: <fqn>`, `patch: "[{op: add, path: /tags/0, value: {tagFQN: PII.Sensitive}}]"` |

## PII Classification Logic

The LLM receives column metadata and classifies using these categories:

| Tag | Description | Example Columns |
|-----|-------------|-----------------|
| `PII.Sensitive` | Directly identifies a person | `email`, `ssn`, `phone_number`, `full_name` |
| `PII.NonSensitive` | Indirectly identifies with context | `zip_code`, `birth_year`, `department` |
| `PersonalData.Personal` | Personal but not identifying | `preferences`, `dietary_restrictions` |
| `Tier.Tier1` | Critical business data | `revenue`, `customer_id`, `order_total` |

## Prompt Template (for LLM)

```
You are a data governance classifier. Given a table's columns with names and descriptions, classify each column.

Table: {table_fqn}
Columns:
{column_list}

For each column, respond with JSON:
[{"column": "name", "tag": "PII.Sensitive|PII.NonSensitive|None", "confidence": 0.0-1.0, "reason": "brief reason"}]

Rules:
- Only suggest PII.Sensitive for columns that directly identify a person
- Confidence must be >0.7 to suggest a tag
- Do not tag columns that are clearly non-personal (e.g., "created_at", "status")
```

## Error Handling

- Table not found → skip, log warning
- Patch fails (auth) → rollback suggestions, report which tables failed
- LLM timeout → retry 2x, then skip
- Low confidence (<0.7) → present to user for manual decision

## Test Cases

1. Table with known PII columns (email, phone) → correctly tagged
2. Table with no PII → returns "No PII detected"
3. Mixed table → tags PII, skips non-PII
4. Auth failure on patch → graceful error, no partial state
