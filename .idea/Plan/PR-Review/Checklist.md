# PR Review Checklist

## For OMH-GSA (Reviewer) — Use on Every PR

### Code Quality

- [ ] Code builds without errors
- [ ] No unused imports or dead code
- [ ] Functions have type hints (Python) / TypeScript types
- [ ] Variable/function names are descriptive
- [ ] No hardcoded secrets, tokens, or URLs
- [ ] Error handling covers expected edge cases
- [ ] Logging present at INFO level for key operations
- [ ] Author confirms `pre-commit run --all-files` is clean locally (no `--no-verify` was used)

### Tests

- [ ] New code has unit tests
- [ ] Tests cover happy path + at least 1 edge case
- [ ] All existing tests still pass
- [ ] Integration test added if touching MCP client or agent

### Documentation

- [ ] Functions have docstrings
- [ ] README updated if new setup steps needed
- [ ] API endpoints documented (if applicable)
- [ ] Architecture docs updated if design changed

### OM Alignment

- [ ] Uses `data-ai-sdk` for MCP interactions (not raw HTTP)
- [ ] Auth handled via environment variables (not hardcoded)
- [ ] MCP tool params match `tools.json` schema exactly
- [ ] UI follows OM design language (colors, typography)

### Security

- [ ] No secrets in commits (check `.env` not committed)
- [ ] JWT tokens not logged at INFO level
- [ ] Input validation on user-facing endpoints
- [ ] No SQL injection vectors (if applicable)

### Architecture Integrity Review (per Feature-Dev SKILL Phase 7)

- [ ] No business logic in `src/copilot/api/` (greppable: no `if confidence`, no `openai.`, no `client.mcp` imports)
- [ ] No HTTP types in `src/copilot/services/` (no `HTTPException`, no `Request`, no `Response`)
- [ ] No business rules in `src/copilot/clients/` (clients only build req → call SDK → map to model → raise typed exception)
- [ ] No N+1 patterns (batch where possible)
- [ ] `tests/architecture/test_layer_imports.py` passes

### Resilience Review (per [Project/NFRs.md §The 5 Things AI Never Adds](../Project/NFRs.md))

- [ ] Every external HTTP/SDK call has explicit `timeout=` (connect + read)
- [ ] Every external call wrapped with `@retry` (`tenacity`) — exponential + jitter
- [ ] Every external call wrapped with a `pybreaker.CircuitBreaker`
- [ ] Circuit-breaker-open path returns the right structured error envelope (`om_unavailable` / `llm_unavailable` / `github_unavailable`)
- [ ] No `requests.*` (use `httpx`); no bare `openai.chat.completions.create()` (use the wrapped client)
- [ ] `tests/integration/test_*_resilience.py` covers each circuit's failure + recovery path

### Observability Review (per [Project/NFRs.md §NFR-06](../Project/NFRs.md))

- [ ] No `print()` (ruff rule T201)
- [ ] No bare `logging.*` (only `structlog` + the redaction processor)
- [ ] Every service entry/exit has a structlog line
- [ ] `request_id` propagated end-to-end (`structlog.contextvars`)
- [ ] New metrics added are exposed on `GET /api/v1/metrics`
- [ ] Sensitive data (secrets, prompts, tool args containing user content) NEVER logged

### AI/ML Security Review — Module G (per [Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md))

- [ ] Any new code that fetches catalog content into an LLM prompt calls `services.prompt_safety.neutralize(field, max_len=...)`
- [ ] Any new tool added to the LLM's available set is added to the `ALLOWED_TOOLS` set in `services/agent.py`
- [ ] Any new write tool (creates/mutates entities or external resources) has `risk_level` set to `soft_write` or `hard_write` and goes through the HITL confirmation gate
- [ ] LLM JSON output is parsed via `ToolCallProposal.model_validate(...)` before any tool execution
- [ ] No `pickle`, `joblib`, `yaml.load(unsafe)`, `eval`, `exec`, or `os.system` introduced
- [ ] `tests/security/test_prompt_injection.py` still covers all 5 canonical patterns; new tests added for any new prompt assembly point

### Merge Criteria

- [ ] All checklist sections above satisfied
- [ ] CI is green (lint, types, tests, pip-audit, bandit, gitleaks per [Security/CIHardening.md](../Security/CIHardening.md))
- [ ] At least 1 approval from OMH-GSA
- [ ] No merge conflicts
- [ ] Branch is rebased on latest `main`
- [ ] If this PR is the last for a phase: corresponding [Validation/QualityGates.md](../Validation/QualityGates.md) gates all green
