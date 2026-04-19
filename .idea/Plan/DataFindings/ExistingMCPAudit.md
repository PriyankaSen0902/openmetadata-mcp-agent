# Existing MCP Server Audit

> **Source**: `openmetadata-mcp/src/main/resources/json/data/mcp/tools.json` (verified April 19, 2026)
> **Module**: `openmetadata-mcp/` — Java, Maven, Lombok, Dropwizard
> **Tool count**: 12 tools, 0 governance-specific tools

## Tool Registry (All 12 Tools)

| #   | Tool Name              | Java Class                         | Description                                                  | Governance Use                                |
| --- | ---------------------- | ---------------------------------- | ------------------------------------------------------------ | --------------------------------------------- |
| 1   | `search_metadata`      | `SearchMetadataTool` (454 LOC)     | Keyword search with OpenSearch DSL, pagination, aggregations | Tag coverage scan, find unclassified entities |
| 2   | `semantic_search`      | `SemanticSearchTool` (280 LOC)     | Vector-based conceptual search using embeddings              | "Find tables about customer spending"         |
| 3   | `get_entity_details`   | `GetEntityTool` (91 LOC)           | Get full entity by FQN                                       | Inspect entity for classification             |
| 4   | `patch_entity`         | `PatchEntityTool` (63 LOC)         | JSON Patch on any entity                                     | **Apply tags, PII labels, descriptions**      |
| 5   | `get_entity_lineage`   | `GetLineageTool` (~100 LOC)        | Upstream/downstream lineage traversal                        | **Impact analysis**                           |
| 6   | `create_lineage`       | `LineageTool` (~80 LOC)            | Create lineage between entities                              | —                                             |
| 7   | `create_glossary`      | `GlossaryTool` (~100 LOC)          | Create glossary                                              | Auto-generate governance glossary             |
| 8   | `create_glossary_term` | `GlossaryTermTool` (~90 LOC)       | Create term in glossary                                      | Auto-generate governance terms                |
| 9   | `get_test_definitions` | `TestDefinitionsTool` (~80 LOC)    | List test definitions                                        | —                                             |
| 10  | `create_test_case`     | `CreateTestCaseTool` (~150 LOC)    | Create test case on table/column                             | Data quality governance                       |
| 11  | `root_cause_analysis`  | `RootCauseAnalysisTool` (~300 LOC) | Upstream failure + downstream impact                         | **Root cause governance**                     |
| 12  | `create_metric`        | `CreateMetricTool` (~250 LOC)      | Create KPI metrics                                           | Governance KPIs                               |

## Tool Registration Mechanism

**File**: `DefaultToolContext.java` (131 LOC)

- Tools registered via **switch-case** in `callTool()` method
- JSON definitions loaded from `json/data/mcp/tools.json`
- Auth via `CatalogSecurityContext` (JWT/OAuth)
- Each tool implements `McpTool` interface: `execute(Authorizer, CatalogSecurityContext, Map<String, Object>)`

## Gaps Identified (What We Fill)

| Gap                                  | Description                                          | Our Solution                                       |
| ------------------------------------ | ---------------------------------------------------- | -------------------------------------------------- |
| **No NL query translation**          | Tools accept structured params, not natural language | LLM agent translates NL → tool params              |
| **No auto-classification**           | No tool scans entities and suggests tags             | Our governance engine scans + LLM classifies       |
| **No governance summary**            | No aggregated governance health view                 | Scan catalog, compute tag coverage %, PII exposure |
| **No multi-MCP orchestration**       | Only connects to OM MCP server                       | LangGraph connects OM + GitHub + Slack MCP servers |
| **No conversational interface**      | Tools are API-only                                   | React chat UI                                      |
| **No lineage-to-impact translation** | `get_entity_lineage` returns raw graph               | LLM generates human-readable impact report         |

## AI SDK Coverage (verified April 19, 2026)

The official Python SDK [`data-ai-sdk`](https://pypi.org/project/data-ai-sdk/) only declares **7 of the 12 tools** as typed `MCPTool` enum members. The remaining 5 are still callable — but only by string name via `client.mcp.call_tool("name", args)`.

**Sources:**

- Enum source: [`open-metadata/ai-sdk` `python/src/ai_sdk/mcp/models.py`](https://github.com/open-metadata/ai-sdk/blob/main/python/src/ai_sdk/mcp/models.py) — `class MCPTool(StrEnum)` lists 7 members
- SDK MCP guide: [`open-metadata/ai-sdk/docs/mcp.md`](https://github.com/open-metadata/ai-sdk/blob/main/docs/mcp.md) — "What are MCP Tools" table lists 7
- Public docs: [docs.open-metadata.org/v1.12.x/sdk/ai-sdk](https://docs.open-metadata.org/v1.12.x/sdk/ai-sdk) — lists 11 (omits `create_metric`)
- MCP server source of truth: [`openmetadata-mcp/src/main/resources/json/data/mcp/tools.json`](../../../openmetadata-mcp/src/main/resources/json/data/mcp/tools.json) — 12 entries

| #   | Tool                   | In `MCPTool` enum?                | How we call it from Python                             |
| --- | ---------------------- | --------------------------------- | ------------------------------------------------------ |
| 1   | `search_metadata`      | ✅ `MCPTool.SEARCH_METADATA`      | `client.mcp.call_tool(MCPTool.SEARCH_METADATA, {...})` |
| 2   | `get_entity_details`   | ✅ `MCPTool.GET_ENTITY_DETAILS`   | typed                                                  |
| 3   | `get_entity_lineage`   | ✅ `MCPTool.GET_ENTITY_LINEAGE`   | typed                                                  |
| 4   | `create_glossary`      | ✅ `MCPTool.CREATE_GLOSSARY`      | typed                                                  |
| 5   | `create_glossary_term` | ✅ `MCPTool.CREATE_GLOSSARY_TERM` | typed                                                  |
| 6   | `create_lineage`       | ✅ `MCPTool.CREATE_LINEAGE`       | typed                                                  |
| 7   | `patch_entity`         | ✅ `MCPTool.PATCH_ENTITY`         | typed                                                  |
| 8   | `semantic_search`      | ❌ string-only                    | `client.mcp.call_tool("semantic_search", {...})`       |
| 9   | `get_test_definitions` | ❌ string-only                    | `client.mcp.call_tool("get_test_definitions", {...})`  |
| 10  | `create_test_case`     | ❌ string-only                    | `client.mcp.call_tool("create_test_case", {...})`      |
| 11  | `create_metric`        | ❌ string-only                    | `client.mcp.call_tool("create_metric", {...})`         |
| 12  | `root_cause_analysis`  | ❌ string-only                    | `client.mcp.call_tool("root_cause_analysis", {...})`   |

**Implication for our agent:** the 5 string-only tools won't appear in `client.mcp.as_langchain_tools()` filtered by `include=[MCPTool.X]`. We have two options:

1. Build thin Python wrappers that call `client.mcp.call_tool("name", args)` and register them as custom LangChain tools (`@tool` decorator)
2. Use `client.mcp.list_tools()` (no filter) → all 12 tool definitions come from the live MCP server, then convert to LangChain `BaseTool` ourselves

We will use **option 1** for the 5 string-only tools and rely on `as_langchain_tools()` for the 7 typed ones. This is documented in `[Architecture/MCPClient.md](../Architecture/MCPClient.md)`.

## Auth & Security Model (Verified from McpServer.java + openmetadata-mcp/README.md)

- OAuth 2.0 Authorization Code Flow with PKCE (RFC 7636) for MCP clients (Claude Desktop, etc.)
- For our service-to-service agent: Bot JWT (Settings → Bots → copy token) sent as `Authorization: Bearer <token>`
- Per-request RBAC via `Authorizer.authorize()` — agent inherits the bot user's permissions
- **Transport: HTTP POST `/mcp` with JSON-RPC 2.0** (stateless streamable HTTP, not SSE; verified in `openmetadata-mcp/README.md` and `open-metadata/ai-sdk/docs/mcp.md`)
- `ImpersonationContext` available for delegated access

## Key Search Parameters (for our MCP client)

```json
// search_metadata — key filters we'll use
{
  "query": "customer tables",
  "entityType": "table",
  "queryFilter": "{\"bool\": {\"must\": [{\"term\": {\"tags.tagFQN\": \"PII.Sensitive\"}}]}}",
  "includeAggregations": true,
  "size": 50
}
```

```json
// patch_entity — how we'll apply tags
{
  "entityType": "table",
  "fqn": "service.database.schema.table",
  "patch": "[{\"op\": \"add\", \"path\": \"/tags/0\", \"value\": {\"tagFQN\": \"PII.Sensitive\", \"source\": \"Manual\"}}]"
}
```
