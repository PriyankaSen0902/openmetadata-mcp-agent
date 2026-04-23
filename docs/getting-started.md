# Getting Started

Get the agent running on your laptop in under 5 minutes.

## Prerequisites

| Tool    | Version | Notes                                      |
| ------- | ------- | ------------------------------------------ |
| Python  | 3.11+   | 3.12 also OK; older versions not supported |
| Node.js | 20+     | For the UI                                 |
| Docker  | Recent  | For OpenMetadata                           |
| Git     | Recent  |                                            |

## Step 1: Clone

```bash
git clone https://github.com/GunaPalanivel/openmetadata-mcp-agent.git
cd openmetadata-mcp-agent
```

## Step 2: Bring up OpenMetadata

You need a running OpenMetadata instance for the agent to call. This repo ships a self-contained Docker Compose stack:

```bash
# One command — starts MySQL, Elasticsearch, and OpenMetadata server
make om-start
# Waits for health automatically; prints next steps when ready.

# Verify manually (optional):
curl -s http://localhost:8585/api/v1/system/version
# Expected JSON includes "version"; admin liveness: curl -sf http://localhost:8586/healthcheck
```

This uses `infrastructure/docker-compose.om.yml` (OM v1.6.2, MySQL 8, Elasticsearch 7.16). Total memory: ~6 GB. Make sure Docker Desktop has at least 8 GB allocated (Settings → Resources).

To stop: `make om-stop`. To check health: `make om-health`. To tail logs: `make om-logs`.

If you already have OpenMetadata running somewhere else, skip this step and set `AI_SDK_HOST` in your `.env` to point to it.

## Step 3: Generate a Bot JWT

The agent authenticates to OpenMetadata's MCP server using a Bot JWT.

### Option A: Automated (recommended)

```bash
# Generates a 30-day JWT and prints it for you to paste into .env
# Tries admin/admin first, then admin@open-metadata.org/admin on basic-auth installs.
make om-gen-token

# Custom expiry (OM 1.6.2 supports 7/30/60/90 days or Unlimited)
python scripts/generate_bot_jwt.py --expiry-days 60

# Custom OM host
python scripts/generate_bot_jwt.py --host http://remote-om:8585

# Custom login identifier for installs with a different principal domain
python scripts/generate_bot_jwt.py --username admin@example.com
```

### Option B: Manual (via OM UI)

1. Open OpenMetadata UI: http://localhost:8585
2. Login with default creds: `admin` / `admin`
3. Go to **Settings -> Bots -> ingestion-bot**
4. Click **Generate New Token**, set expiry to 30 days, copy the token

> **Security**: Do NOT paste the token in any GitHub comment, issue, or PR.

## Step 4: Configure secrets

```bash
make setup
# Edit .env with your editor; paste:
#   AI_SDK_TOKEN=<the JWT from step 3>
#   OPENAI_API_KEY=<your OpenAI key from platform.openai.com/api-keys>
```

## Step 5: Install + run

```bash
# Install Python deps + UI deps
make install_dev_env

# One-time: install pre-commit hooks (lint, format, gitleaks, license headers).
# These run on every `git commit` and are required for PRs to merge.
pip install pre-commit
pre-commit install
pre-commit run --all-files   # initial bulk run

# Start backend + UI
make demo
# Backend: http://127.0.0.1:8000  (FastAPI docs at /api/v1/docs)
# UI:      http://localhost:3000
```

UI-only checks (port `:3000`, console clean): [`ui/README.md`](../ui/README.md). `make install_dev_env` runs `npm ci` under `ui/` using the committed lockfile.

## Step 6: Verify

In a new terminal:

```bash
python scripts/smoke_test.py --include-om
```

Should print `smoke: all green`. If it doesn't, check `[Troubleshooting](#troubleshooting)` below.

In the UI, click **Check backend health** — should show `status: ok`.

---

## Troubleshooting

### `OPENAI_API_KEY not set`

You forgot to copy `.env.example` to `.env` or didn't paste a real key. Fix:

```bash
make setup
# edit .env
```

### OpenMetadata returns 401

Bot JWT is expired or wrong. Regenerate it (Step 3) and update `.env`.

### Docker container won't start (OOM)

OpenMetadata needs ~8 GB RAM. In Docker Desktop -> Settings -> Resources, increase memory to 8 GB and restart Docker.

### Port 8585 / 8000 / 3000 already in use

Another process is bound. Either kill it (`lsof -i :8000`) or override the port in `.env` (backend) / `vite.config.ts` (UI).

### CI fails on first push

This is expected for the first push because some dependencies need to actually install in CI. Re-run the failed workflow once and it usually goes green. If it persists, check the workflow logs and file an issue with the failed job name.

---

## Next

- Read [`CLAUDE.md`](../CLAUDE.md) for the architectural contract.
- Read [`CodePatterns.md`](../CodePatterns.md) before writing code.
- See [`docs/architecture.md`](architecture.md) for the system context diagram.
- See [`docs/api.md`](api.md) for the FastAPI surface.
- See [`docs/runbook.md`](runbook.md) for operations.

For internal planning docs (PRD, ADRs, NFRs, threat model, etc.), browse [`.idea/Plan/`](../.idea/Plan/README.md).
