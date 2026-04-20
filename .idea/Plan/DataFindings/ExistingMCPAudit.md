# Existing MCP Server Audit — Complete Tool Schema Reference

> **Last updated**: April 20, 2026
> **Author**: @PriyankaSen0902 (Senior Builder)
> **Issue**: [#20 — P1-07](https://github.com/GunaPalanivel/openmetadata-mcp-agent/issues/20)
> **Server source of truth**: [`openmetadata-mcp/src/main/resources/json/data/mcp/tools.json`](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json) (12 entries)
> **SDK source**: [`open-metadata/ai-sdk`](https://github.com/open-metadata/ai-sdk) v0.1.2 — Python package [`data-ai-sdk`](https://pypi.org/project/data-ai-sdk/)

---

## Summary: All 12 MCP Tools

| # | Tool Name | In `MCPTool` Enum? | Category | Required Params | Optional Params | Governance Use |
|---|-----------|-------------------|----------|-----------------|-----------------|----------------|
| 1 | `search_metadata` | ✅ `SEARCH_METADATA` | Read | _(none)_ | query, entityType, queryFilter, from, size, includeDeleted, fields, includeAggregations, maxAggregationBuckets | Tag coverage scan, find unclassified entities |
| 2 | `semantic_search` | ✅ `SEMANTIC_SEARCH` | Read | query | filters, size, k, threshold | "Find tables about customer spending" |
| 3 | `get_entity_details` | ✅ `GET_ENTITY_DETAILS` | Read | entityType, fqn | _(none)_ | Inspect entity for classification |
| 4 | `get_entity_lineage` | ✅ `GET_ENTITY_LINEAGE` | Read | entityType, fqn | upstreamDepth, downstreamDepth | **Impact analysis** |
| 5 | `create_glossary` | ✅ `CREATE_GLOSSARY` | Write | name, description, mutuallyExclusive | owners, reviewers | Auto-generate governance glossary |
| 6 | `create_glossary_term` | ✅ `CREATE_GLOSSARY_TERM` | Write | glossary, name, description | parentTerm, owners, reviewers | Auto-generate governance terms |
| 7 | `create_lineage` | ✅ `CREATE_LINEAGE` | Write | fromEntity, toEntity | _(none)_ | Create lineage edges |
| 8 | `patch_entity` | ✅ `PATCH_ENTITY` | Write | entityType, fqn, patch | _(none)_ | **Apply tags, PII labels, descriptions** |
| 9 | `get_test_definitions` | ✅ `GET_TEST_DEFINITIONS` | Read | entityType | testPlatform, after, limit | List available DQ test types |
| 10 | `create_test_case` | ✅ `CREATE_TEST_CASE` | Write | name, fqn, testDefinitionName, parameterValues | columnName, entityType, description | Data quality governance |
| 11 | `root_cause_analysis` | ✅ `ROOT_CAUSE_ANALYSIS` | Read | fqn, entityType | upstreamDepth, downstreamDepth, queryFilter, includeDeleted | **Root cause + downstream impact** |
| 12 | `create_metric` | ❌ **String-only** | Write | name, metricExpressionLanguage, metricExpressionCode | description, displayName, metricType, granularity, unitOfMeasurement, customUnitOfMeasurement, owners, reviewers, relatedMetrics, tags, domains | Governance KPIs |

---

## Typed vs String-Callable Split

> **CORRECTION**: The SDK `docs/mcp.md` table lists only 7 tools, but the **actual source code** in `models.py` contains **11 typed enum members**. Only `create_metric` is string-only.

### 11 Typed Enum Tools — reachable via `MCPTool.X`

```python
# Source: https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/models.py
from ai_sdk.mcp.models import MCPTool

class MCPTool(StrEnum):
    SEARCH_METADATA = "search_metadata"
    SEMANTIC_SEARCH = "semantic_search"
    GET_ENTITY_DETAILS = "get_entity_details"
    GET_ENTITY_LINEAGE = "get_entity_lineage"
    CREATE_GLOSSARY = "create_glossary"
    CREATE_GLOSSARY_TERM = "create_glossary_term"
    CREATE_LINEAGE = "create_lineage"
    PATCH_ENTITY = "patch_entity"
    GET_TEST_DEFINITIONS = "get_test_definitions"
    CREATE_TEST_CASE = "create_test_case"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
```

**How to call**: `client.mcp.call_tool(MCPTool.SEARCH_METADATA, {"query": "customers"})`

### 1 String-Callable Tool — reachable via `client.mcp.call_tool("name", args)`

| Tool | Why not in enum? | How to call |
|------|-----------------|-------------|
| `create_metric` | Not yet added to `MCPTool` StrEnum in SDK v0.1.2 | `client.mcp.call_tool("create_metric", {...})` |

**Implication for our agent**: The 1 string-only tool (`create_metric`) won't appear in `client.mcp.as_langchain_tools()` filtered by `include=[MCPTool.X]`. We need a thin Python wrapper registered as a custom LangChain tool (`@tool` decorator). All other 11 tools work natively.

---

## Per-Tool Detailed Schemas

### Tool 1: `search_metadata`

> **Source**: [tools.json L8–L106](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.SEARCH_METADATA`

**Description**: Keyword-based search for data assets. Best when you know specific names, owners, tags, tiers, services, or column names. Supports pagination and advanced OpenSearch DSL queries.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | — | Natural language search query. Examples: "tables owned by marketing" |
| `entityType` | string | No | — | Filter by entity type (singular form): table, dashboard, topic, pipeline, database, databaseService, glossary, glossaryTerm, mlmodel, container, chart, metric, user, team, domain, dataProduct |
| `queryFilter` | string | No | — | Advanced OpenSearch JSON query string. Overrides `query` when provided. Must include entityType filter |
| `from` | integer | No | 0 | Pagination offset |
| `size` | integer | No | 10 | Results per page (max 50) |
| `includeDeleted` | boolean | No | false | Include deleted entities |
| `fields` | string | No | — | Comma-separated additional fields (e.g. "columns,queries") |
| `includeAggregations` | boolean | No | false | Include facet aggregations |
| `maxAggregationBuckets` | integer | No | 10 | Max aggregation buckets (max 50) |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains search hits with `fullyQualifiedName` and `entityType` fields.

---

### Tool 2: `semantic_search`

> **Source**: [tools.json L107–L168](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.SEMANTIC_SEARCH`

**Description**: Meaning-based discovery using vector embeddings. Best for exploratory queries where you don't know exact names — finds conceptually related assets.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | **Yes** | — | Natural language query describing what you're looking for |
| `filters` | object | No | — | Filter object: `{"entityType": ["table"], "service": ["BigQuery"], "tags": ["PII.Sensitive"]}` |
| `size` | integer | No | 10 | Number of parent entities to return (max 50) |
| `k` | integer | No | 100 | KNN nearest neighbors parameter |
| `threshold` | number | No | 0.0 | Minimum similarity score (0.0–1.0) |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains entity summaries with name, columns, description, fullyQualifiedName, entityType.

---

### Tool 3: `get_entity_details`

> **Source**: [tools.json L169–L190](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.GET_ENTITY_DETAILS`

**Description**: Get detailed information about a specific entity by FQN. Use `fullyQualifiedName` and `entityType` from search results directly.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entityType` | string | **Yes** | — | Type of entity (table, dashboard, topic, pipeline, etc.) |
| `fqn` | string | **Yes** | — | Fully qualified name from search results |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains full entity details optimized for LLM context.

---

### Tool 4: `get_entity_lineage`

> **Source**: [tools.json L303–L335](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.GET_ENTITY_LINEAGE`

**Description**: Get upstream/downstream dependency information. Use for root cause or impact analysis.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entityType` | string | **Yes** | — | Type of entity |
| `fqn` | string | **Yes** | — | Fully qualified name |
| `upstreamDepth` | integer | No | 3 | Upstream hops to traverse (max 10) |
| `downstreamDepth` | integer | No | 3 | Downstream hops to traverse (max 10) |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains lineage graph with nodes and edges.

---

### Tool 5: `create_glossary`

> **Source**: [tools.json L236–L276](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.CREATE_GLOSSARY`

**Description**: Creates a new Glossary — a collection of terms defining business vocabulary.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Glossary name |
| `description` | string | **Yes** | — | Glossary description |
| `mutuallyExclusive` | boolean | **Yes** | false | Whether child terms are mutually exclusive |
| `owners` | array[string] | No | — | OM User or Team names |
| `reviewers` | array[string] | No | — | OM User or Team names for approval workflow |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains created glossary entity.

---

### Tool 6: `create_glossary_term`

> **Source**: [tools.json L191–L235](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.CREATE_GLOSSARY_TERM`

**Description**: Creates a new Glossary Term. Must belong to an existing Glossary. Supports hierarchical terms.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `glossary` | string | **Yes** | — | Parent glossary FQN |
| `name` | string | **Yes** | — | Term name |
| `description` | string | **Yes** | — | Term description |
| `parentTerm` | string | No | — | Parent term FQN for hierarchy (format: `<glossary>.<parent>...<term>`) |
| `owners` | array[string] | No | — | OM User or Team names |
| `reviewers` | array[string] | No | — | OM User or Team names for approval workflow |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains created glossary term entity.

---

### Tool 7: `create_lineage`

> **Source**: [tools.json L336–L379](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.CREATE_LINEAGE`

**Description**: Creates lineage relationship between two assets.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fromEntity` | object | **Yes** | — | Source entity: `{"type": "<entityType>", "id": "<uuid>"}` |
| `fromEntity.type` | string | **Yes** | — | Entity type of source |
| `fromEntity.id` | string | **Yes** | — | UUID of source entity |
| `toEntity` | object | **Yes** | — | Destination entity: `{"type": "<entityType>", "id": "<uuid>"}` |
| `toEntity.type` | string | **Yes** | — | Entity type of destination |
| `toEntity.id` | string | **Yes** | — | UUID of destination entity |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains created lineage edge.

---

### Tool 8: `patch_entity`

> **Source**: [tools.json L277–L302](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.PATCH_ENTITY`

**Description**: Patches an entity using JSONPatch (RFC 6902). Array fields use PLURAL names: `domains`, `owners`, `tags`, `reviewers`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entityType` | string | **Yes** | — | Entity type to patch |
| `fqn` | string | **Yes** | — | Fully qualified name |
| `patch` | string | **Yes** | — | JSONPatch operations as JSON array string |

**Patch examples**:
```json
// Add a PII tag
[{"op": "add", "path": "/tags/0", "value": {"tagFQN": "PII.Sensitive", "source": "Manual"}}]

// Update description
[{"op": "add", "path": "/description", "value": "new description"}]

// Add domain
[{"op": "add", "path": "/domains/0", "value": {"id": "<domain-uuid>", "type": "domain", "name": "<domain-name>"}}]
```

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains patched entity.

---

### Tool 9: `get_test_definitions`

> **Source**: [tools.json L380–L408](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.GET_TEST_DEFINITIONS`

**Description**: Get all test definitions. Used to discover available tests before creating test cases.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entityType` | string | **Yes** | — | `TABLE` or `COLUMN` |
| `testPlatform` | string | No | — | Platform: OpenMetadata, GreatExpectations, DBT, Deequ, Soda, Other |
| `after` | string | No | — | Pagination cursor (from response `nextCursor`) |
| `limit` | integer | No | 10 | Max results per page |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains list of test definitions with `parameterDefinition` (name, description, dataType, required).

---

### Tool 10: `create_test_case`

> **Source**: [tools.json L409–L471](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.CREATE_TEST_CASE`

**Description**: Creates a test case for a table or column. Requires test definitions from `get_test_definitions`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Test case name |
| `fqn` | string | **Yes** | — | Table FQN (always table, not column) |
| `testDefinitionName` | string | **Yes** | — | FQN of the test definition |
| `parameterValues` | array[object] | **Yes** | — | Array of `{"name": "<param>", "value": "<value>"}` |
| `columnName` | string | No | — | Column name for column-level tests (just name, not FQN) |
| `entityType` | string | No | — | Entity type (default: table) |
| `description` | string | No | — | Test case description |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains created test case entity.

---

### Tool 11: `root_cause_analysis`

> **Source**: [tools.json L558–L598](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: `MCPTool.ROOT_CAUSE_ANALYSIS`

**Description**: Comprehensive root cause analysis via data quality lineage. Identifies upstream failures, then automatically analyzes downstream impact.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fqn` | string | **Yes** | — | Entity FQN to analyze |
| `entityType` | string | **Yes** | — | Entity type (see full list in tools.json) |
| `upstreamDepth` | integer | No | 3 | Upstream traversal depth |
| `downstreamDepth` | integer | No | 3 | Downstream traversal depth |
| `queryFilter` | string | No | — | Elasticsearch query filter |
| `includeDeleted` | boolean | No | false | Include deleted entities |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains:
- `status`: "failed" (upstream failures found) or "success" (no failures)
- `upstreamAnalysis`: nodes and edges leading to failures
- `downstreamAnalysis`: impacted downstream nodes (only if status=failed)

---

### Tool 12: `create_metric` ⚠️ STRING-ONLY

> **Source**: [tools.json L472–L557](https://github.com/open-metadata/OpenMetadata/blob/main/openmetadata-mcp/src/main/resources/json/data/mcp/tools.json)
> **Enum**: ❌ Not in `MCPTool` — call via `client.mcp.call_tool("create_metric", {...})`

**Description**: Creates a Metric entity (KPI). Supports SQL, Python, Java, JavaScript expressions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Metric name (unique, no `::`) |
| `metricExpressionLanguage` | string | **Yes** | — | Enum: SQL, Java, JavaScript, Python, External |
| `metricExpressionCode` | string | **Yes** | — | Code/query computing the metric |
| `description` | string | No | — | Markdown description |
| `displayName` | string | No | — | Human-readable display name |
| `metricType` | string | No | — | Enum: COUNT, SUM, AVERAGE, RATIO, PERCENTAGE, MIN, MAX, MEDIAN, MODE, STANDARD_DEVIATION, VARIANCE, OTHER |
| `granularity` | string | No | — | Enum: SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR |
| `unitOfMeasurement` | string | No | — | Enum: COUNT, DOLLARS, PERCENTAGE, TIMESTAMP, SIZE, REQUESTS, EVENTS, TRANSACTIONS, OTHER |
| `customUnitOfMeasurement` | string | No | — | Required when unitOfMeasurement is OTHER |
| `owners` | array[string] | No | — | OM usernames or team names |
| `reviewers` | array[string] | No | — | OM usernames or team names |
| `relatedMetrics` | array[string] | No | — | FQNs of related metrics |
| `tags` | array[string] | No | — | Tag FQNs (e.g. "Tier.Tier1", "PII.Sensitive") |
| `domains` | array[string] | No | — | Domain FQNs |

**Response shape**: `ToolCallResult(success=True, data={...}, error=None)` where `data` contains created metric entity.

---

## SDK Data Models

> **Source**: [`models.py`](https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/models.py)

```python
@dataclass
class ToolParameter:
    name: str
    type: str          # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool

@dataclass
class ToolInfo:
    name: MCPTool           # Tool identifier (enum)
    description: str        # Human-readable description
    parameters: list[ToolParameter]

@dataclass
class ToolCallResult:
    success: bool           # Whether the call succeeded
    data: dict | None       # Result data (if success)
    error: str | None       # Error message (if failed)
```

## SDK Client API (`MCPClient`)

> **Source**: [`_client.py`](https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/_client.py)

| Method | Returns | Description |
|--------|---------|-------------|
| `list_tools()` | `list[ToolInfo]` | Fetch available tools via JSON-RPC `tools/list`. Note: only returns tools matching `MCPTool` enum (11 of 12) |
| `call_tool(name, arguments)` | `ToolCallResult` | Execute tool via JSON-RPC `tools/call`. Accepts `MCPTool` enum |
| `as_langchain_tools(include, exclude)` | `list[BaseTool]` | Convert to LangChain format. Requires `pip install data-ai-sdk[langchain]` |
| `as_openai_tools(include, exclude)` | `list[dict]` | Convert to OpenAI function calling format |
| `create_tool_executor()` | `Callable[[str, dict], dict]` | Create executor for OpenAI tool calls |

**Transport**: HTTP POST `/mcp` with JSON-RPC 2.0 (stateless, not SSE).

**Key implementation detail** (`_client.py` line 140–150): `_parse_tool_info()` returns `None` for tools not recognized by the SDK enum. This means `list_tools()` silently drops `create_metric` — it returns 11 tools, not 12.

## Framework Adapters

### LangChain Adapter
> **Source**: [`_langchain.py`](https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/_langchain.py)

- Converts `ToolInfo` → `BaseTool` subclass with dynamic Pydantic `args_schema`
- MCP types mapped: string→str, integer→int, number→float, boolean→bool, array→list, object→dict
- Error handling: `MCPToolExecutionError` → `ToolException`

```python
# Read-only tools
tools = client.mcp.as_langchain_tools(
    include=[MCPTool.SEARCH_METADATA, MCPTool.GET_ENTITY_DETAILS, MCPTool.GET_ENTITY_LINEAGE]
)

# All tools except mutations
tools = client.mcp.as_langchain_tools(
    exclude=[MCPTool.PATCH_ENTITY, MCPTool.CREATE_GLOSSARY, MCPTool.CREATE_GLOSSARY_TERM]
)
```

### OpenAI Adapter
> **Source**: [`_openai.py`](https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/_openai.py)

- Converts `ToolInfo` → OpenAI function calling schema dict
- `create_tool_executor()` returns a callable that maps tool name → `MCPTool` enum → `call_tool()`

## Auth & Security Model

> **Source**: `McpServer.java` + `openmetadata-mcp/README.md`

- OAuth 2.0 Authorization Code Flow with PKCE (RFC 7636) for MCP clients (Claude Desktop, etc.)
- For service-to-service agent: Bot JWT (Settings → Bots → copy token) sent as `Authorization: Bearer <token>`
- Per-request RBAC via `Authorizer.authorize()` — agent inherits the bot user's permissions
- **Transport: HTTP POST `/mcp` with JSON-RPC 2.0** (stateless streamable HTTP)
- `ImpersonationContext` available for delegated access

## Key Search Parameter Examples

```json
// search_metadata — tag coverage scan
{
  "query": "*",
  "entityType": "table",
  "queryFilter": "{\"bool\": {\"must_not\": [{\"exists\": {\"field\": \"tags.tagFQN\"}}]}}",
  "size": 50,
  "includeAggregations": true
}
```

```json
// search_metadata — find PII-tagged entities
{
  "queryFilter": "{\"bool\": {\"must\": [{\"term\": {\"entityType\": \"table\"}}, {\"term\": {\"tags.tagFQN\": \"PII.Sensitive\"}}]}}",
  "size": 50
}
```

```json
// patch_entity — apply PII tag
{
  "entityType": "table",
  "fqn": "service.database.schema.table",
  "patch": "[{\"op\": \"add\", \"path\": \"/tags/0\", \"value\": {\"tagFQN\": \"PII.Sensitive\", \"source\": \"Manual\"}}]"
}
```

## Gaps Identified (What We Fill)

| Gap | Description | Our Solution |
|-----|-------------|-------------|
| **No NL query translation** | Tools accept structured params, not natural language | LLM agent translates NL → tool params |
| **No auto-classification** | No tool scans entities and suggests tags | Our governance engine scans + LLM classifies |
| **No governance summary** | No aggregated governance health view | Scan catalog, compute tag coverage %, PII exposure |
| **No multi-MCP orchestration** | Only connects to OM MCP server | LangGraph connects OM + GitHub + Slack MCP servers |
| **No conversational interface** | Tools are API-only | React chat UI |
| **No lineage-to-impact translation** | `get_entity_lineage` returns raw graph | LLM generates human-readable impact report |
| **`create_metric` not in enum** | Only 11 of 12 tools are typed | Custom `@tool` wrapper for `create_metric` |
