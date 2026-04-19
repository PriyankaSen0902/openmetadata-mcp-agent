<!--
Thanks for opening a PR. Please fill in the sections below.

Reviewer routing is automatic (see `.github/workflows/auto-assign-reviewer.yml`):
  - Team PR (Priyanka, Aravind, Bhawika)         -> @GunaPalanivel reviews
  - Outside contributor / fork PR                -> @PriyankaSen0902 reviews
  - PR opened by @GunaPalanivel                  -> @PriyankaSen0902 reviews

The reviewer walks this PR against `.idea/Plan/PR-Review/Checklist.md`.

BEFORE pushing: run `pre-commit run --all-files` locally. Do not use `--no-verify`.
-->

## Summary

<!-- 2-3 sentences: what does this PR do, and why? -->

## Linked task / issue

<!-- Reference TaskSync IDs and/or GitHub issues, e.g. P2-06, #26645 -->

- TaskSync: `P_-_`
- Closes: #

## Changes

- <!-- list specific changes; group by file or layer -->
-
-

## How to test

1. <!-- step-by-step verification instructions -->
2.
3.

## Screenshots / recordings

<!-- For UI changes, include a before/after screenshot or a short loom/gif. -->

## Author checklist

### Code Quality

- [ ] `pre-commit run --all-files` is clean locally (no `--no-verify`)
- [ ] Code builds without errors
- [ ] No unused imports / dead code
- [ ] Type hints on all Python signatures (`mypy --strict` passes)
- [ ] No `any` in TypeScript; no `as any` casts
- [ ] No `console.log` / `print()` in production paths
- [ ] No hardcoded secrets or URLs
- [ ] Names are descriptive (`is_active` not `flag`, `classify_columns` not `process`)

### Architecture Integrity (per `CodingStandards.md` Three Laws)

- [ ] Code is in the correct layer (api / services / clients / models)
- [ ] No business logic in `src/copilot/api/` (greppable: no `if confidence`, no `openai.`, no `client.mcp` imports)
- [ ] No HTTP types (`HTTPException`, `Request`, `Response`) in `src/copilot/services/`
- [ ] No business rules in `src/copilot/clients/`
- [ ] `tests/architecture/test_layer_imports.py` still passes

### Resilience (per `NFRs.md` "The 5 Things AI Never Adds")

- [ ] Every new external HTTP/SDK call has explicit `timeout=`
- [ ] Every new external call wrapped with `@retry` (`tenacity`)
- [ ] Every new external call wrapped with a `pybreaker.CircuitBreaker`
- [ ] Circuit-breaker-open path returns the right structured error envelope
- [ ] No `requests.*` (use `httpx`); no bare `openai.chat.completions.create()`

### Observability (per `NFRs.md` NFR-06)

- [ ] No `print()` (ruff rule T201)
- [ ] No bare `logging.*` — only `structlog`
- [ ] Every service entry/exit has a structlog line
- [ ] `request_id` propagated end-to-end
- [ ] New metrics exposed on `GET /api/v1/metrics`
- [ ] Sensitive data NEVER logged (use redaction processor)

### AI/ML Security — Module G (per `Security/PromptInjectionMitigation.md`)

- [ ] Any new code that fetches catalog content into an LLM prompt calls `services.prompt_safety.neutralize(...)`
- [ ] Any new tool added to the LLM's available set is added to `ALLOWED_TOOLS` in `services/agent.py`
- [ ] Any new write tool has `risk_level` set to `soft_write` or `hard_write` and goes through the HITL confirmation gate
- [ ] LLM JSON output is parsed via `ToolCallProposal.model_validate(...)` before any tool execution
- [ ] No `pickle`, `joblib`, `yaml.load(unsafe)`, `eval`, `exec`, or `os.system` introduced
- [ ] `tests/security/test_prompt_injection.py` still covers all 5 canonical patterns

### Tests

- [ ] New code has unit tests (happy path + at least one failure case)
- [ ] All existing tests still pass (`make test`)
- [ ] Integration test added if touching MCP client or agent
- [ ] Test coverage stays above 70% on `src/copilot/`

### Documentation

- [ ] Functions have docstrings
- [ ] README updated if new setup steps needed
- [ ] API endpoints documented in `docs/api.md` (if applicable)
- [ ] Architecture docs updated if design changed (`.idea/Plan/Architecture/*.md`)
- [ ] CHANGELOG.md entry added under `[Unreleased]`

### Security

- [ ] No secrets in commits (gitleaks clean)
- [ ] JWT tokens / API keys never logged
- [ ] Input validation on user-facing endpoints
- [ ] License header (`LICENSE_HEADER.txt`) added to every new source file

### Phase exit (only if this PR closes the last task in a phase)

- [ ] All gates from `.idea/Plan/Validation/QualityGates.md` for the current phase are green

## Reviewer checklist

- [ ] All sections of the author checklist are honestly filled in
- [ ] CI is green (lint, types, tests, security scan, secret scan, UI build, path-guard)
- [ ] No merge conflicts
- [ ] Branch is rebased on latest `main`

---

**Reviewer**: assigned automatically by `.github/workflows/auto-assign-reviewer.yml`
