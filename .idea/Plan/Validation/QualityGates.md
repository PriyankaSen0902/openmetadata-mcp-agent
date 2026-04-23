# Quality Gates

> Phase 7 deliverable per [Feature-Dev SKILL.md §Phase 7](../../agents/Feature-Dev/SKILL.md). Run before declaring ANY phase complete. Each section is a checklist; every NO blocks phase exit.

## Gate 0: Automated checks (must pass)

```
[ ] pytest tests/unit/ -v        — all green
[ ] pytest --cov=src/copilot --cov-fail-under=70   — coverage threshold met
[ ] ruff check src/ tests/       — zero errors
[ ] ruff format --check src/ tests/   — zero diffs
[ ] mypy --strict src/copilot    — zero errors
[ ] pip-audit --strict           — zero CVEs in installed deps
[ ] bandit -r src/copilot -ll    — zero medium+ findings
[ ] gitleaks detect              — zero secrets
[ ] cd ui && npm ci && npm run build && npx tsc --noEmit   — UI builds + types clean
```

CI runs all of the above per [Security/CIHardening.md](../Security/CIHardening.md). Local dev: `make ci-local`.

### Sixteen-issue program linkage

When closing the **16 engineering** issues ([FeatureDev/GovernanceEngine.md](../FeatureDev/GovernanceEngine.md)), each PR should reference its issue number. Gate exit for Phase 2–3 product work is **not** declared until the issues in **W1–W3** that own the touched surfaces are closed or explicitly descoped in [TaskSync.md](../TaskSync.md) with a reason.

---

## Gate 1: Architecture Integrity Review

> Per [Feature-Dev SKILL §Phase 7 — Architecture Integrity Review](../../agents/Feature-Dev/SKILL.md). Verifies layer separation per [Architecture/CodingStandards.md §Law 1](../Architecture/CodingStandards.md).

```
[ ] No business logic in src/copilot/api/
    -> grep "if.*confidence" src/copilot/api/ should be empty
    -> grep "openai\.\|client.mcp" src/copilot/api/ should be empty (only services use clients)

[ ] No direct DB / external SDK calls from src/copilot/api/
    -> All external interactions go through src/copilot/clients/

[ ] No HTTP knowledge in src/copilot/services/
    -> grep "HTTPException\|Request\|Response" src/copilot/services/ should be empty
    -> grep "fastapi\." src/copilot/services/ should only show DI imports (Depends)

[ ] No business rules in src/copilot/clients/
    -> Clients only do: build request, call SDK, map response to domain model, raise typed exception

[ ] All external I/O has timeout
    -> grep "httpx.AsyncClient(" src/copilot/clients/ -A 2 — every one has timeout=
    -> grep "openai.AsyncOpenAI(" src/copilot/clients/ -A 2 — every one has timeout=
    -> grep "AISdk(" src/copilot/clients/ — uses settings.om_timeout_seconds

[ ] No N+1 query patterns
    -> Auto-classification batches columns per table; doesn't hit OM once per column
    -> Lineage impact uses single get_entity_lineage call per root, not per node

[ ] Layer-import test passes
    -> tests/architecture/test_layer_imports.py
```

---

## Gate 2: Security Review

> Per [Feature-Dev SKILL §Phase 7 — Security Review](../../agents/Feature-Dev/SKILL.md) plus our [Security/ControlCoverage.md](../Security/ControlCoverage.md). Re-walk the SC-N claims from [Security/ThreatModel.md](../Security/ThreatModel.md).

```
[ ] SC-1 — FastAPI binds to 127.0.0.1 (Settings.host check + tests/security/test_bind_local.py)
[ ] SC-2 — Three secrets loaded via SecretStr; no string literals in src/
    -> rg "OPENAI_API_KEY\|AI_SDK_TOKEN\|GITHUB_TOKEN" src/ — only env access, no literals
[ ] SC-3 — HITL gate enforced for every soft_write/hard_write tool call
    -> tests/security/test_hitl_gate.py
[ ] SC-4 — LLM JSON output is Pydantic-validated before tool execution
    -> tests/security/test_llm_invalid_output.py
[ ] SC-5 — Tool allowlist enforced server-side (not just LLM-side)
    -> tests/security/test_tool_allowlist.py
[ ] SC-6 — Catalog content neutralized + truncated before LLM prompt
    -> tests/security/test_prompt_injection.py covers 5 injection patterns
[ ] SC-7 — Every external call has timeout + retry + circuit breaker
    -> tests/integration/test_om_resilience.py, test_openai_resilience.py
[ ] SC-8 — Error envelopes never echo secrets/paths/exceptions
    -> tests/security/test_error_envelope_safety.py
[ ] SC-9 — No pickle/joblib/yaml.load(unsafe)/eval/exec/os.system
    -> bandit -r src/copilot -ll passes
[ ] SC-10 — No upstream OM repo modifications
    -> git diff main..HEAD -- ../OpenMetadata/openmetadata-mcp/ is empty (or N/A — separate repo)

[ ] All user inputs validated at API boundary (Pydantic models)
[ ] No SQL — but if any added later, parameterized only
[ ] CORS configured to specific origins (http://localhost:3000), not *
[ ] Rate limiting on /chat (30 req/min per IP) per NFR-04
```

---

## Gate 3: Resilience Review

> Per [Feature-Dev SKILL §Phase 7 — Resilience Review](../../agents/Feature-Dev/SKILL.md). Verifies the 5 Things AI Never Adds from [Project/NFRs.md](../Project/NFRs.md).

```
[ ] Every external call has timeout
    -> grep -rn "httpx.AsyncClient\|openai.AsyncOpenAI\|AISdk(" src/copilot/clients/ — all have timeout=

[ ] Every external call has retry
    -> grep -rn "@retry" src/copilot/clients/ — present on every call function
    -> Retry config matches NFRs.md Section "1. Retry logic" exactly

[ ] Every external call has circuit breaker
    -> grep -rn "@om_breaker\|@openai_breaker\|@github_breaker" src/copilot/clients/

[ ] Graceful degradation on circuit open
    -> When OM breaker opens, /chat returns om_unavailable envelope (not crash)
    -> When OpenAI breaker opens, /chat returns llm_unavailable envelope
    -> tests/integration/test_*_circuit_open.py asserts each path

[ ] Database connection pooling configured
    -> N/A in v1 (no DB)

[ ] Health check endpoint exists and works
    -> GET /api/v1/healthz returns 200 normally, 503 when degraded
    -> tests/integration/test_healthz.py covers both
```

---

## Gate 4: Observability Review

> Per [Feature-Dev SKILL §Phase 7 — Observability Review](../../agents/Feature-Dev/SKILL.md). Verifies [NFRs.md §NFR-06](../Project/NFRs.md).

```
[ ] structlog initialized at process startup with the redaction processor
    -> src/copilot/observability/__init__.py
    -> Redaction processor wired with all 3 secret values (SecretsHandling.md)

[ ] Every service entry/exit has a structlog line
    -> grep -rn "log.info\|log.warning\|log.error" src/copilot/services/

[ ] request_id propagated end-to-end
    -> Middleware src/copilot/middleware/request_id.py generates UUID and binds to structlog contextvars
    -> Verify: rg request_id logs/agent.log shows the same ID across an entire chat turn

[ ] No print() in production code paths
    -> ruff rule T201 enabled
    -> grep -rn "print(" src/copilot/ should be empty

[ ] No bare logging.* — only structlog
    -> grep -rn "import logging\|from logging" src/copilot/ shows only structlog wiring

[ ] /metrics endpoint exposes the 4 Golden Signals
    -> Prometheus text format
    -> Series: agent_requests_total, agent_errors_total, agent_request_latency_seconds, agent_llm_tokens_used_total
    -> tests/integration/test_metrics_endpoint.py asserts each series present
```

---

## Gate 5: AI/ML Security Review (Module G)

> Per [security-vulnerability-auditor SKILL §Module G](../../agents/security-vulnerability-auditor/SKILL.md) + our [Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md).

```
[ ] No pickle/joblib/yaml(unsafe) anywhere — JSON serialization only
    -> Already covered by SC-9 in Gate 2

[ ] Models / prompts version-controlled (in src/copilot/services/prompts/, not external storage)

[ ] Every catalog field that enters an LLM prompt passes through neutralize()
    -> grep -rn "neutralize(" src/copilot/services/ — all 6 callers (per PromptInjectionMitigation.md)

[ ] LLM output validated with Pydantic before tool execution
    -> services/llm_validator.py raises LlmInvalidOutput on parse failure

[ ] Tool allowlist enforced server-side (defense-in-depth beyond Literal type)
    -> services/agent.py::execute_proposal raises ToolNotAllowlisted

[ ] Token budget enforced per session
    -> ChatSession tracks tokens_used; raises LlmTokenBudgetExceeded at cap

[ ] HITL gate for soft_write and hard_write
    -> Already covered by SC-3 in Gate 2

[ ] PII redaction processor strips secret values from log lines
    -> Already covered by SC-2 in Gate 2

[ ] tests/security/test_prompt_injection.py covers all 5 canonical patterns
```

---

## Per-phase exit gate matrix

| Phase                            | Gates required to pass exit                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Phase 1 — Foundation**         | Gate 0 + Gate 1 (Architecture Integrity)                                                          |
| **Phase 2 — Core Features**      | Gate 0 + Gate 1 + Gate 2 (Security) + Gate 3 (Resilience) for the auto-classify and lineage flows |
| **Phase 3 — Polish + Multi-MCP** | All five gates (0, 1, 2, 3, 4) + Gate 5 (AI/ML Security) for the multi-MCP write paths            |
| **Phase 4 — Submit**             | All five gates + [Validation/PRR.md](./PRR.md) PRR-lite checklist                                 |

A phase that does not pass its required gates does not exit. No "we'll fix it next phase" — that's how technical debt compounds and how Sriharsha-persona spots a sloppy submission.

## Who runs what

| Gate                            | Owner                                          |
| ------------------------------- | ---------------------------------------------- |
| Gate 0 — Automated              | CI (every push); local: `make ci-local`        |
| Gate 1 — Architecture Integrity | OMH-GSA (reviewer) per PR                      |
| Gate 2 — Security               | OMH-GSA (security audit per phase)             |
| Gate 3 — Resilience             | OMH-PSTL (writes the resilience tests)         |
| Gate 4 — Observability          | OMH-PSTL (writes the observability assertions) |
| Gate 5 — AI/ML Security         | OMH-GSA (owns the prompt-safety code)          |

## Why this discipline matters for first prize

Per [JudgePersona.md](../Project/JudgePersona.md): Suresh and Sriharsha will not be impressed by an LLM novelty demo. They will be impressed by a system that has been built with explicit gates, where every "the LLM might do X" question has a Pydantic-validated, circuit-broken, HITL-gated, structured-error answer. This file is the contract the team holds itself to.
