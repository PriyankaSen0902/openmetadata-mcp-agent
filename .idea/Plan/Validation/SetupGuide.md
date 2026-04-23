# Local Setup Guide

## Prerequisites

| Tool    | Version | Install                          |
| ------- | ------- | -------------------------------- |
| Python  | 3.11+   | [python.org](https://python.org) |
| Node.js | 18+     | [nodejs.org](https://nodejs.org) |
| Docker  | 24+     | [docker.com](https://docker.com) |
| Git     | 2.30+   | System default                   |

## Step 1: Clone the Repository

```bash
git clone https://github.com/GunaPalanivel/openmetadata-mcp-agent.git
cd openmetadata-mcp-agent
```

## Step 2: Start OpenMetadata (Docker)

```bash
# From this repo root (OM 1.6.2 + MySQL + Elasticsearch; migrate runs before server)
make om-start
# or: bash scripts/start_om.sh

# Wait for OM to be ready (check health)
curl -s http://localhost:8585/api/v1/system/version

# Expected: JSON with a "version" field
```

## Step 3: Generate Bot JWT Token

1. Open OpenMetadata UI: `http://localhost:8585`
2. Login with default creds: `admin` / `admin`
3. Go to **Settings → Bots → ingestion-bot**
4. Copy the JWT token
5. Save to `.env` file:

```bash
AI_SDK_HOST=http://localhost:8585
AI_SDK_TOKEN=<paste-jwt-here>
```

## Step 4: Install Python Dependencies

```bash
cd openmetadata-mcp-agent/
pip install -e ".[dev]"
```

## Step 4b: Install Pre-Commit Hooks (Required)

Pre-commit runs the same lint, format, secret-scan, and license-header checks as CI. Install once per clone:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

If a hook auto-modifies a file (for example, ruff fixes a lint error or end-of-file-fixer adds a newline), the commit is rejected. Re-stage the modified files and commit again. Never use `--no-verify` to bypass.

The hook set is defined in [`.pre-commit-config.yaml`](../../../.pre-commit-config.yaml) and includes:

- `ruff` (lint + auto-fix) and `ruff-format`
- `gitleaks` (secret scanning)
- standard hygiene hooks (trailing whitespace, end-of-file fixer, YAML/large-files/private-key checks, `no-commit-to-branch --branch main`)
- local Apache 2.0 license-header check

## Step 5: Verify MCP Connection

```bash
python -c "
from ai_sdk import AISdk, AISdkConfig
config = AISdkConfig.from_env()
client = AISdk.from_config(config)
result = client.mcp.call_tool('search_metadata', {'query': '*', 'size': 1})
print('✅ MCP Connected:', result)
"
```

## Step 6: Start the Chat UI

```bash
cd ui/
npm ci
npm run dev
# → http://localhost:3000
```

Use committed `package-lock.json` (`npm ci`). Full P1-14 checklist: [`ui/README.md`](../../ui/README.md).

## Step 7: Start the Agent Backend

```bash
cd openmetadata-mcp-agent/
uvicorn copilot.api:app --reload --port 8000
# → http://localhost:8000/docs
```

## Troubleshooting

| Issue                    | Fix                                                       |
| ------------------------ | --------------------------------------------------------- |
| OM Docker fails to start | Check Docker Desktop is running, increase RAM to 8GB      |
| JWT token expired        | Re-generate from Settings → Bots                          |
| MCP connection refused   | Verify OM is up: `curl -s localhost:8585/api/v1/system/version` or `curl -sf localhost:8586/healthcheck` |
| UI can't connect         | Check API URL in `.env` matches backend port              |
