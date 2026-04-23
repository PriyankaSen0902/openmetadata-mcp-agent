# Demo Failure Recovery

> **Linked from**: TaskSync **P2-13b**, **P3-14**, **P3-16**, **P4-03c**.
> **Companion**: [Narrative.md](./Narrative.md), [SubmissionChecklist.md](./SubmissionChecklist.md).

## The frozen seed dataset

**Artifact**: [`seed/customer_db.json`](../../seed/customer_db.json) (50+ tables).

**Why frozen:** Judges and CI need a **deterministic** catalog: known PII columns, Tier-1 markers, and **two prompt-injection planted** column descriptions. Do not “fix” injection strings in seed during the hackathon week unless security tests are updated in the same PR.

**Load + index:**

1. `make om-gen-token` (or equivalent) + `.env` with OM URL and `AI_SDK_TOKEN`.
2. `python scripts/load_seed.py` (see [seed/README.md](../../seed/README.md)).
3. Run search reindex helper if search returns empty: `scripts/trigger_om_search_reindex.py`.

**Verify:** `search_metadata` returns seeded tables by keyword (e.g. `customer_db`).

## Three-rehearsal protocol (P3-14)

| Rehearsal                   | Intent                                                                                   | Pass criteria                                                                                    |
| --------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **R1 — Happy path**         | Run [Narrative.md](./Narrative.md) Scenes 1–2 end-to-end.                                | No 5xx; HITL confirm succeeds if write flow on.                                                  |
| **R2 — Failure at Scene 2** | Stop OM container mid-lineage query OR revoke token.                                     | UI + API return **structured** error (`om_unavailable` / `om_auth_failed`); no stack in browser. |
| **R3 — Backup machine**     | Cold clone on second laptop per [Validation/SetupGuide.md](../Validation/SetupGuide.md). | Clone → run in **< 15 min** (stretch **< 5 min** by Phase 3 exit).                               |

## The backup recording (P3-16)

- **Primary**: `demo/final_recording.mp4` (1920×1080, 2–3 min).
- **Backup**: `demo/backup_recording.mp4` — record same script **immediately after** primary; store on **different disk** or cloud.
- **Verify**: Both files play start-to-end on a third device (phone/tablet) **night before** submission.

## Pre-conditions checklist (P4-03c)

- [ ] OM + ES healthy (`GET /api/v1/healthz` green for configured checks).
- [ ] OpenAI quota / key valid (or Codex path documented).
- [ ] `npm ci` + `pip install` reproducible from lockfiles.
- [ ] Browser cache cleared or incognito (avoid stale Vite HMR).
- [ ] Clock sync OK (JWT / `expires_at` on proposals).

## Fallback scripts (spoken lines)

| Failure  | Say this                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- |
| OM down  | “We’re hitting the local OpenMetadata stack — here’s the structured error envelope the agent returns instead of a white screen.” |
| LLM down | “Circuit breaker is open; the agent degrades gracefully per NFRs.”                                                               |
| UI only  | “Backend is live — I’ll drive the same contract via Swagger `POST /api/v1/chat`.”                                                |

## After-incident

1. Capture `request_id` from JSON envelope.
2. Pull structlog line (redacted).
3. File issue in repo with `[demo-fail]` prefix if post-mortem needed.
