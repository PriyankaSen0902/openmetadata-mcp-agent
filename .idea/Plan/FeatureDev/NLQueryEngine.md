# NL Query Engine Feature Spec

## Owner: OMH-PSTL (Priyanka)
## Phase: 2 (Day 5–7)

---

## Overview

Translate natural language queries into the correct MCP tool calls, execute them, and return structured, human-readable responses.

## User Flow Examples

```
User: "Show me all tables owned by the data-eng team"
→ Agent selects: search_metadata
→ Params: queryFilter={"bool":{"must":[{"term":{"entityType":"table"}},{"nested":{"path":"owners","query":{"term":{"owners.name":"data-eng"}}}}]}}
→ Returns: formatted table with name, FQN, service, tier

User: "Find tables related to customer purchase behavior"
→ Agent selects: semantic_search (conceptual query, not keyword)
→ Params: query="customer purchase behavior", filters={"entityType":["table"]}
→ Returns: ranked results with similarity scores

User: "Tell me about the orders table"
→ Agent selects: get_entity_details
→ Params: entityType="table", fqn="<detected_fqn>"
→ Returns: columns, tags, owners, description, service
```

## Tool Selection Logic

```python
def select_tool(user_query: str) -> str:
    """Agent uses LLM to decide which tool to call."""
    # The LLM receives all 12 tool descriptions and picks the best match.
    # Key routing rules:
    # - Exact names, owners, tags, filters → search_metadata
    # - Conceptual/vague queries → semantic_search
    # - "Tell me about X" → get_entity_details
    # - "What depends on X?" → get_entity_lineage
    # - "What's broken?" → root_cause_analysis
```

## Response Formatting

All responses rendered as structured Markdown:

```markdown
### Search Results (12 found)

| # | Name | Service | Tier | Tags |
|---|------|---------|------|------|
| 1 | customers | BigQuery | Tier1 | PII.Sensitive |
| 2 | orders | Snowflake | Tier2 | — |

> 💡 Use "tell me about <name>" to get full details.
```

## MCP Tools Used

| Scenario | Tool | Key Params |
|----------|------|------------|
| Keyword search | `search_metadata` | `query`, `entityType`, `queryFilter` |
| Conceptual search | `semantic_search` | `query`, `filters`, `threshold` |
| Entity details | `get_entity_details` | `entityType`, `fqn` |
| Lineage query | `get_entity_lineage` | `entityType`, `fqn`, `upstreamDepth`, `downstreamDepth` |

## Error Handling

- No results → "No results found. Try a broader search or different keywords."
- Ambiguous query → "Did you mean: [option A] or [option B]?"
- Auth failure → "You don't have permission to view this entity."
- MCP timeout → Retry 2x, then "OpenMetadata server is not responding. Please try again."

## Test Cases

1. "Show me tier 1 tables" → `search_metadata` with tier filter → results
2. "Tables about revenue" → `semantic_search` → ranked results
3. "What is dim_customers?" → `get_entity_details` → full entity
4. "How many tables in BigQuery?" → `search_metadata` with aggregation → count
5. Empty result → graceful message
