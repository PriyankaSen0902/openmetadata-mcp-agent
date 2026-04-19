# Production Readiness Review (Hackathon-Scoped)

> Phase 8 deliverable per [Feature-Dev SKILL.md §Phase 8](../../agents/Feature-Dev/SKILL.md). Scoped down for a 7-day hackathon submission, not a real production deployment. Run the day before submission (Apr 25).

## Purpose

Even though this project is NOT going into production, the discipline of running a PRR lifts the submission to a level Suresh and Sriharsha will recognize ([JudgePersona.md](../Project/JudgePersona.md)). The judges will not see this file directly, but they WILL see its outputs: a runbook, a healthz endpoint, alerting thresholds in `/metrics`, and a clean rollback path.

## Adapted from Google PRR + Amazon ORR

The standard checklist scaled down for the hackathon scope. Skipped items are explicitly marked N/A with reason.

### Ownership and Accountability

```
[ ] On-call team identified
    -> Demo-day operator: OMH-GSA. Backup: OMH-ATL.
    -> See Project/Runbook.md "Demo-day morning checklist".

[ ] Escalation path documented
    -> If demo fails: switch to backup recording per Demo/FailureRecovery.md
    -> If submission portal fails: email contact@wemakedevs.org

[ ] SLOs defined (availability, latency, error rate)
    -> Hackathon SLO: zero unhandled exceptions during the 5-min demo window
    -> Latency: p95 /chat < 8s for multi-step queries (per NFRs.md NFR-01)
    -> Error rate: < 5% during demo (anything higher = abort and switch to recording)
```

### Observability

```
[ ] Four Golden Signals instrumented
    -> agent_request_latency_seconds (Latency)
    -> agent_requests_total (Traffic)
    -> agent_errors_total (Errors)
    -> agent_circuit_breaker_state, agent_pending_confirmations (Saturation)
    -> Per Architecture/APIContract.md GET /api/v1/metrics

[ ] Dashboards exist
    -> Prometheus + Grafana out of scope for v1
    -> Substitute: GET /metrics returns Prometheus text format; can be screenshotted for the demo if needed
    -> Substitute: structlog JSON to logs/agent.log; can be tailed live in a side terminal

[ ] Alert thresholds set
    -> N/A in v1 — no monitoring stack
    -> Manual: demo-day operator watches the side terminal for ERROR-level lines
```

### Reliability

```
[ ] Load tested at 10x expected traffic
    -> N/A — single-user demo; documented in Discovery.md as out of scope

[ ] Rollback plan documented AND tested
    -> See Project/Runbook.md "Rollback to known-good state"
    -> Each Phase Exit creates a git tag (v0.1.0-phase1, v0.2.0-phase2, etc.)
    -> Rollback in <2 min: git checkout <tag> && docker compose down && docker compose up

[ ] Database backup and restore procedure
    -> N/A — no database in v1
    -> Seed data (seed/customer_db.json) is in version control; restore = git checkout

[ ] Disaster recovery plan
    -> Backup demo machine prepared per RiskRegister.md R-02
    -> Backup pre-recorded video per Demo/FailureRecovery.md
```

### Security

```
[ ] Dependency vulnerability scan passed
    -> pip-audit --strict in CI must be zero CVEs (Security/CIHardening.md)

[ ] Penetration test passed
    -> N/A for hackathon. Forward-looking ThreatModel.md covers attacker scenarios.

[ ] Secret rotation strategy documented
    -> Security/SecretsHandling.md "Rotation" section covers all 3 secrets

[ ] All data in transit encrypted (TLS 1.2+)
    -> Outbound: data-ai-sdk -> OM, openai -> OpenAI, github_mcp -> GitHub all use HTTPS
    -> Inbound: FastAPI bound to 127.0.0.1 only; no TLS termination needed for loopback in v1

[ ] PII handling compliant with regulatory requirements
    -> N/A — no PII processed; only metadata (column names, descriptions)
    -> See Discovery.md "Sensitive Data" row
```

### Deployment

```
[ ] CI/CD pipeline automated and tested
    -> .github/workflows/ci.yml per Security/CIHardening.md
    -> Last 5 runs all green before submission

[ ] Blue-green or rolling deployment
    -> N/A — laptop-only demo deployment

[ ] Feature flags for gradual rollout
    -> N/A — no rollout

[ ] Rollback achievable in <5 minutes
    -> Yes — Project/Runbook.md "Rollback to known-good state": <2 min
```

### Documentation

```
[ ] README: clone -> run in <5 minutes
    -> openmetadata-mcp-agent/README.md verified by OMH-BSE on a clean machine
    -> See Validation/SetupGuide.md for the exact command sequence

[ ] Runbook: what to do when each alert fires
    -> Project/Runbook.md covers 8 failure modes

[ ] Architecture doc: current and accurate
    -> Architecture/Overview.md updated; matches actual code at the time of submission
    -> Mermaid diagrams render in GitHub markdown preview

[ ] API doc: complete and versioned
    -> Architecture/APIContract.md
    -> Auto-generated OpenAPI at /api/v1/docs
```

## Hackathon-specific PRR

Items not in standard PRR but critical for hackathon judging.

```
[ ] Demo script rehearsed end-to-end on the demo machine — at least 3 dry runs
    -> Demo/Narrative.md timing rehearsed; OMH-BSE owns this

[ ] Backup recording exists and plays cleanly
    -> demo/backup_recording.mp4 verified in browser

[ ] Frozen seed dataset loads in <60s on the demo machine
    -> seed/customer_db.json + scripts/load_seed.py
    -> Verified by smoke test the morning of demo (Project/Runbook.md "Demo-day morning checklist")

[ ] Submission package complete
    -> Hackathon form fields ready: project name, repo URL, demo video URL, team members, AI disclosure, track
    -> See Demo/SubmissionChecklist.md

[ ] Intent comments posted on #26645 and #26608
    -> TaskSync.md P0-01 and P0-02 confirmed done

[ ] OpenMetadata GitHub repo starred by all four team members
    -> Hackathon side-quest requirement (per #27444)

[ ] Repo is public and Apache 2.0 licensed
    -> openmetadata-mcp-agent/LICENSE checked in

[ ] AI disclosure in README
    -> "Built with OpenAI GPT-4o-mini via LangGraph + data-ai-sdk"

[ ] No .env or secrets in git history
    -> gitleaks detect from beginning of repo: 0 findings
```

## Sign-off

Before P4-04 (submission), OMH-GSA records here:

```
PRR run on: 2026-04-25 ____ IST
Items passed: __ / __
Items waived (with reason): __
Sign-off: @GunaPalanivel
```

If any item is unchecked at submission time and not explicitly waived with a documented reason, do NOT submit until resolved.

## Why this is a competitive moat

Most hackathon submissions will have:

- A README with setup instructions
- A demo video
- A repo

Few will have:

- A documented PRR
- A documented runbook
- A documented rollback procedure
- A documented failure-mode catalog
- A documented risk register

Per [JudgePersona.md](../Project/JudgePersona.md), absence of a runbook is a tell. Presence of a runbook that the operator actually follows on demo day is the kind of signal that wins Best Use of OpenMetadata + Technical Excellence simultaneously.
