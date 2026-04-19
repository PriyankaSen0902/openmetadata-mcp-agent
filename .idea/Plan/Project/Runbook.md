# Runbook

> Phase 9 deliverable per [Feature-Dev SKILL.md](../../agents/Feature-Dev/SKILL.md). What to do when each thing breaks. Designed for the demo-day operator (OMH-GSA) and any teammate filling in.

## Demo-day morning checklist (run at 9 AM IST on Apr 26)

```
[ ] OM Docker container responds at http://localhost:8585/api/v1/health (status: healthy)
[ ] Bot JWT token is fresh (regenerated this morning, expires > 24h from now)
[ ] `python scripts/smoke_test.py` runs 5 representative chat queries successfully
[ ] OpenAI account 1 quota check: `python scripts/check_openai_quota.py` returns >$2 remaining
[ ] OpenAI account 2 (rotation backup) — same check
[ ] Backup demo machine (OMH-PSTL's laptop) up + verified with same smoke test
[ ] Backup recording at `demo/backup_recording.mp4` plays cleanly in browser
[ ] Browser bookmarks set: chat UI, FastAPI /docs, /metrics, OM UI Settings → Bots
[ ] Phone on silent, screen-share notifications off, do-not-disturb on
[ ] Internet check: speedtest.net > 10 Mbps up/down
```

If any item is RED, escalate per [RiskRegister.md](./RiskRegister.md) and do NOT start recording.

---

## Failure mode 1: OpenAI returns 429 RateLimitError

**Symptom**: Every chat turn returns `{"code":"llm_unavailable",...}` after 2 retries.

**Diagnose**:

```bash
tail -f logs/agent.log | rg llm_unavailable
# Look for: "OpenAI rate limit hit"
```

**Mitigate (3 minutes)**:

1. Edit `.env`: swap `OPENAI_API_KEY` to the backup account's key
2. Restart agent backend: `make restart-agent`
3. Verify: `python scripts/smoke_test.py`

If both accounts are exhausted: `make demo-cached` to serve from `seed/demo_responses.json` and disclose to judges.

---

## Failure mode 2: OpenMetadata MCP returns 401 (JWT expired)

**Symptom**: Every tool call returns `{"code":"om_auth_failed",...}`; logs show `MCPError(status_code=401)`.

**Diagnose**:

```bash
curl -H "Authorization: Bearer $AI_SDK_TOKEN" http://localhost:8585/api/v1/system/version
# 401 → token expired or wrong
```

**Mitigate (1 minute)**:

1. Open `http://localhost:8585` → Settings → Bots → `ingestion-bot`
2. Click "Generate New Token", expiry = 30 days
3. Copy token, paste into `.env` as `AI_SDK_TOKEN=...`
4. Restart agent backend: `make restart-agent`

---

## Failure mode 3: OM container crashes / unhealthy

**Symptom**: `curl http://localhost:8585/api/v1/health` hangs or returns 5xx.

**Diagnose**:

```bash
docker compose -f infrastructure/docker-compose.yml ps
docker logs openmetadata_server --tail 100
```

**Mitigate**:

- If OOM: increase Docker Desktop memory to 10 GB; `docker compose restart openmetadata_server`
- If port conflict on 8585: `lsof -i :8585`; kill the offender; restart compose
- If MySQL is the broken dep: `docker compose restart openmetadata_mysql && sleep 30 && docker compose restart openmetadata_server`
- If unrecoverable in 3 min: switch to backup demo machine (per [RiskRegister.md R-02](./RiskRegister.md))

---

## Failure mode 4: LLM returns malformed JSON (LLM-invalid-output)

**Symptom**: Agent enters confirmation gate but the proposed-actions list is empty or shape-invalid; UI shows "AI returned an unexpected response".

**Diagnose**:

```bash
rg llm_invalid_output logs/agent.log -A 5
# Look for: "Pydantic validation failed: expected ToolCallProposal..."
```

**Mitigate**:

- Single-turn flake: re-submit (retry is cheap)
- Repeated: switch to GPT-4o (higher-quality, more expensive) by editing `MODEL=gpt-4o-mini` → `MODEL=gpt-4o` in `.env` and restarting agent
- Persistent across multiple queries: prompt template likely regressed — `git log --oneline src/copilot/services/prompts/` and revert if needed

---

## Failure mode 5: Auto-classification suggests obviously-wrong tags

**Symptom**: Demo runs `auto-classify PII in customer_db` and the agent suggests tagging `created_at` as PII.Sensitive.

**Diagnose**:

- Inspect the actual prompt sent: `rg "classification_prompt" logs/agent.log -A 30`
- Likely cause: column descriptions or names contain misleading content (or a prompt-injection attempt landed)

**Mitigate**:

- HITL gate works as designed: just say "no" to the wrong tag in the UI (this is the demo point — judges SEE the gate working)
- If multiple wrong tags, kill the chat session: `POST /chat/cancel` and start fresh
- Long-term fix: tighten the prompt template's `Rules:` section in `src/copilot/services/prompts/classification.py`

---

## Failure mode 6: GitHub MCP fails (Phase 3 multi-MCP demo)

**Symptom**: "find PII tables → create GitHub issue" workflow fails on the GitHub step.

**Diagnose**:

```bash
rg github_mcp logs/agent.log -A 5
# Look for: 401 (PAT bad), 404 (repo wrong), 422 (validation)
```

**Mitigate**:

- Verify `GITHUB_TOKEN` PAT is valid and has `issues:write` scope on the demo repo
- Verify repo exists: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/repos/GunaPalanivel/openmetadata-mcp-agent`
- Circuit breaker per NFR-T2 will open after 3 failures and degrade gracefully — UI will say "GitHub is unavailable; PII findings preserved at /chat/last-result"
- Worst case: skip the multi-MCP scene; demo Scenes 1-3 still tell the story

---

## Failure mode 7: UI does not connect to backend

**Symptom**: Chat UI loads but `Send` button shows network error in browser devtools.

**Diagnose**:

- Browser devtools → Network tab → look at `POST /chat` response
- Common: `VITE_API_URL` in `ui/.env` does not match backend port

**Mitigate**:

- Confirm backend running: `curl http://localhost:8000/healthz` should return `{"status":"ok"}`
- Confirm CORS: backend FastAPI must include `CORSMiddleware` allowing `http://localhost:3000`
- Verify `ui/.env`: `VITE_API_URL=http://localhost:8000`
- Restart UI: `cd ui && npm run dev`

---

## Failure mode 8: Demo recording machine starts thrashing during demo

**Symptom**: Cursor lags, audio glitches, OBS dropping frames.

**Mitigate**:

- Close every non-essential app BEFORE recording (Slack, Discord, Spotify, IDEs not in demo)
- If mid-recording: pause, restart recording, splice in post; OBS scene-cut is faster than full retake

---

## Rollback to known-good state

```bash
# Tag a known-good commit at end of every phase
git tag -a v0.1.0-phase1 -m "phase 1 exit gate green"
git tag -a v0.2.0-phase2 -m "phase 2 exit gate green"
# etc.

# To rollback in <2 minutes:
git stash
git checkout v0.2.0-phase2
docker compose down && docker compose up -d
make demo
```

---

## Where to find each thing on demo day

| Need                       | Location                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| Bot JWT                    | OM UI → Settings → Bots → `ingestion-bot` → Token                                              |
| Backup OpenAI key          | Encrypted file `secrets/backup_openai.key` (1Password / Bitwarden)                             |
| GitHub PAT                 | OMH-GSA's GitHub Settings → Developer Settings → PATs (fine-grained, scoped to demo repo only) |
| Backup recording           | `demo/backup_recording.mp4`                                                                    |
| Frozen seed data           | `seed/customer_db.json` (loaded by `scripts/load_seed.py`)                                     |
| Demo script                | [Demo/Narrative.md](../Demo/Narrative.md)                                                      |
| Failure-recovery procedure | [Demo/FailureRecovery.md](../Demo/FailureRecovery.md)                                          |
| This runbook               | `docs/runbook.md` in the standalone repo (mirror of this doc)                                  |

---

## Post-demo housekeeping

```
[ ] Stop OBS / screen recorder
[ ] Save recording to demo/recording_YYYYMMDD.mp4
[ ] Backup recording to cloud (Drive / Dropbox)
[ ] Submit hackathon form on WeMakeDevs
[ ] Comment on #26645 + #26608 with the submission link
[ ] Post a thank-you in OM Slack
[ ] Team retro within 48 hours (per TaskSync.md P4-08)
```
