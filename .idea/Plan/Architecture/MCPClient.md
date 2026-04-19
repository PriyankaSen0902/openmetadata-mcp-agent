# MCP Client Design

## Connection Architecture

```
data-ai-sdk → SSE → {OM_HOST}/mcp → OM MCP Server (Java)
                     ↑
                     JWT in Authorization header
```

## Configuration

```bash
# .env file
AI_SDK_HOST=http://localhost:8585
AI_SDK_TOKEN=<paste-bot-jwt-from-OM-UI-Settings-Bots>  # gitleaks:allow
OPENAI_API_KEY=<paste-from-platform.openai.com>        # gitleaks:allow
```

## SDK Setup

```python
from ai_sdk import AISdk, AISdkConfig

config = AISdkConfig.from_env()
client = AISdk.from_config(config)

# LangChain integration
tools = client.mcp.as_langchain_tools()

# Direct call
result = client.mcp.call_tool("search_metadata", {
    "query": "customer tables",
    "entityType": "table",
    "size": 20
})
```

## Tool Schema (from tools.json)

The MCP server exposes 12 tools. Key tools for governance:

| Tool | Required Params | Optional Params |
|------|----------------|-----------------|
| `search_metadata` | — | `query`, `entityType`, `queryFilter`, `size`, `from`, `fields` |
| `semantic_search` | `query` | `filters`, `size`, `k`, `threshold` |
| `get_entity_details` | `entityType`, `fqn` | — |
| `patch_entity` | `entityType`, `fqn`, `patch` | — |
| `get_entity_lineage` | `entityType`, `fqn` | `upstreamDepth`, `downstreamDepth` |
| `root_cause_analysis` | `fqn`, `entityType` | `upstreamDepth`, `downstreamDepth` |

## Transport Layer

- **Protocol**: SSE (Server-Sent Events) over HTTP
- **Auth**: JWT Bearer token in every request
- **Endpoint**: `{host}/mcp` (handled internally by SDK)
- **Reconnection**: SDK handles SSE reconnects automatically
