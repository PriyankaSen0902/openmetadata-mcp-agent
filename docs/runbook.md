# Runbook

What to do when the agent breaks. For internal team use during development and demos.

## Demo-day morning checklist

Run at 9 AM on demo day:

```bash
# Backend reachable?
python scripts/smoke_test.py --include-om
# Expected: smoke: all green

# OpenAI key present?
python scripts/check_openai_quota.py
# Expected: OK: OPENAI_API_KEY present (sk-***xxxx)

# Bot JWT fresh? (manually verify expiry > 24h via OM UI -> Settings -> Bots -> ingestion-bot)
```

If any check fails RED, escalate per the relevant section below. Do NOT start recording until all green.

---

## Failure mode 1: OpenAI returns 429 (rate limit / quota exhausted)

Symptom: every chat turn returns `{"code":"llm_unavailable",...}` after 2 retries.

Diagnose:

```bash
tail -f logs/agent.log | grep llm_unavailable
```

Mitigate (3 minutes):

1. Edit `.env`: swap `OPENAI_API_KEY` to a backup account's key
2. Restart: `make restart-agent`
3. Verify: `python scripts/smoke_test.py`

If both keys exhausted: switch to demo-cached mode (returns pre-baked answers from `seed/demo_responses.json` if present) and disclose to judges.

---

## Failure mode 2: OpenMetadata MCP returns 401 (JWT expired)

Symptom: every tool call returns `{"code":"om_auth_failed",...}`.

Diagnose:

```bash
curl -H "Authorization: Bearer $AI_SDK_TOKEN" http://localhost:8585/api/v1/system/version
# 401 -> token expired or wrong
```

Mitigate (1 minute):

1. OM UI -> Settings -> Bots -> `ingestion-bot` -> "Generate New Token", expiry 30 days
2. Copy token into `.env` as `AI_SDK_TOKEN=...`
3. `make restart-agent`

---

## Failure mode 3: OpenMetadata Docker crashes / unhealthy

Symptom: `curl http://localhost:8586/healthcheck` fails or `curl http://localhost:8585/api/v1/system/version` hangs or returns 5xx.

Diagnose:

```bash
docker compose -f infrastructure/docker-compose.om.yml ps -a
docker compose -f infrastructure/docker-compose.om.yml logs --tail 100 openmetadata-migrate
docker compose -f infrastructure/docker-compose.om.yml logs --tail 100 openmetadata-server
```

Mitigate:

- If OOM: increase Docker Desktop memory to 10 GB; restart compose
- If port 8585 conflict: `lsof -i :8585`, kill the offender, restart compose
- If MySQL is the broken dep: `docker compose -f infrastructure/docker-compose.om.yml restart openmetadata-mysql`, wait 30s, then `docker compose -f infrastructure/docker-compose.om.yml up -d` (re-runs migrate if needed)
- If migrate failed (empty DB / missing tables): `docker compose -f infrastructure/docker-compose.om.yml down -v` then `make om-start` for a clean bootstrap
- If unrecoverable in 3 min: switch to backup demo machine

---

## Failure mode 4: LLM returns malformed JSON (`llm_invalid_output`)

Symptom: agent enters confirmation gate but proposed-actions list is empty or shape-invalid; UI shows "AI returned an unexpected response".

Diagnose:

```bash
grep llm_invalid_output logs/agent.log -A 5
```

Mitigate:

- One-off flake: re-submit (retry is cheap)
- Repeated: switch to higher-quality model in `.env` (`OPENAI_MODEL=gpt-4o`); restart
- Persistent across queries: prompt template likely regressed — `git log --oneline src/copilot/services/prompts/` and revert if needed

---

## Failure mode 5: GitHub MCP fails (Phase 3 multi-MCP demo)

Symptom: "find PII tables -> create GitHub issue" workflow fails on the GitHub step.

Diagnose:

```bash
grep github_mcp logs/agent.log -A 5
# Look for: 401 (PAT bad), 404 (repo wrong), 422 (validation)
```

Mitigate:

- Verify `GITHUB_TOKEN` PAT is valid + has `issues:write` on the demo repo
- Verify repo exists: `gh repo view GunaPalanivel/openmetadata-mcp-agent`
- Circuit breaker degrades gracefully — UI shows "GitHub is unavailable; PII findings preserved at /chat/last-result"
- Worst case: skip the multi-MCP scene; demo Scenes 1-3 still tell the story

---

## Failure mode 6: UI does not connect to backend

Symptom: chat UI loads but Send button shows network error in browser devtools.

Diagnose:

- Browser devtools -> Network tab -> look at `POST /chat` response
- Common: `VITE_API_URL` in `ui/.env` does not match backend port

Mitigate:

- Confirm backend running: `curl http://127.0.0.1:8000/api/v1/healthz`
- Confirm CORS: backend FastAPI must include `CORSMiddleware` allowing `http://localhost:3000`
- Verify `ui/.env`: `VITE_API_URL=http://localhost:8000`
- Install UI deps from lockfile, then restart: `cd ui && npm ci && npm run dev` (see [`ui/README.md`](../ui/README.md))

---

## Rollback to known-good state

```bash
# Tag a known-good commit at the end of every phase
git tag -a v0.1.0-phase1 -m "phase 1 exit gate green"

# To rollback in <2 minutes:
git stash
git checkout v0.1.0-phase1
make demo
```

---

## Post-demo housekeeping

```
[ ] Stop OBS / screen recorder
[ ] Save recording to demo/recording_YYYYMMDD.mp4
[ ] Backup recording to cloud (Drive / Dropbox)
[ ] Submit hackathon form on WeMakeDevs
[ ] Comment on #26645 + #26608 with the submission link
[ ] Star the upstream OpenMetadata repo
[ ] Team retro within 48 hours
```

---

For internal context (risk register, demo failure recovery procedure with backup video, full failure-mode matrix), see [`.idea/Plan/Project/Runbook.md`](../.idea/Plan/Project/Runbook.md) and [`.idea/Plan/Project/RiskRegister.md`](../.idea/Plan/Project/RiskRegister.md).
