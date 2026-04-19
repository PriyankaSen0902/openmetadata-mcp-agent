# API Analysis

> Key OpenMetadata REST API endpoints wrapped by the MCP tools we'll use.

## MCP Tool → API Mapping

| MCP Tool | OM REST Endpoint | Method | Key Params |
|----------|-----------------|--------|------------|
| `search_metadata` | `/api/v1/search/query` | GET | `q`, `index`, `size`, `from` |
| `semantic_search` | `/api/v1/search/semantic` | POST | `query`, `filters`, `k` |
| `get_entity_details` | `/api/v1/{entityType}/name/{fqn}` | GET | `fields` |
| `patch_entity` | `/api/v1/{entityType}/name/{fqn}` | PATCH | JSON Patch body |
| `get_entity_lineage` | `/api/v1/lineage/getLineage` | GET | `fqn`, `type`, `upstreamDepth` |
| `create_glossary` | `/api/v1/glossaries` | POST | `name`, `description` |
| `create_glossary_term` | `/api/v1/glossaryTerms` | POST | `glossary`, `name` |
| `root_cause_analysis` | `/api/v1/lineage/getLineage` + search | Composite | `fqn`, search for test failures |
| `create_metric` | `/api/v1/metrics` | POST | `name`, `expression` |
| `create_test_case` | `/api/v1/dataQuality/testCases` | POST | `fqn`, `testDefinitionName` |

## Auth Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/users/login` | Login, get JWT |
| `/api/v1/bots/{name}/token` | Get bot JWT |
| `/api/v1/config/auth` | Auth config |

## Key Entity Types

| Entity Type | Index Name | Use In Project |
|-------------|-----------|----------------|
| `table` | `table_search_index` | Primary target for classification |
| `dashboard` | `dashboard_search_index` | Lineage downstream |
| `pipeline` | `pipeline_search_index` | Lineage nodes |
| `topic` | `topic_search_index` | Streaming governance |
| `glossaryTerm` | `glossary_term_search_index` | Auto-generated terms |

## SDK Connection Pattern

```python
from ai_sdk import AISdk, AISdkConfig

# Via environment variables
# AI_SDK_HOST=http://localhost:8585
# AI_SDK_TOKEN=<bot-jwt-token>
config = AISdkConfig.from_env()
client = AISdk.from_config(config)

# Get LangChain-compatible tools
tools = client.mcp.as_langchain_tools()

# Direct tool call
result = client.mcp.call_tool("search_metadata", {"query": "customer tables", "entityType": "table"})
```
