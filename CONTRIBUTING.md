# Contributing to openmetadata-mcp-agent

Thanks for your interest. Quick guide to get a PR through review.

## Setup

Follow [`docs/getting-started.md`](docs/getting-started.md) for the full clone-to-run path (under 5 minutes).

After `make install_dev_env`, install the pre-commit hooks before your first commit:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files   # one-time bulk run; safe to skip after first PR
```

This is mandatory. The same hooks run in CI, and a PR that does not pass them locally will not pass CI either. The hooks include:

- `ruff` (lint + auto-fix) and `ruff-format`
- `gitleaks` (secret scanning across staged content)
- `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-added-large-files`, `check-merge-conflict`, `check-case-conflict`, `detect-private-key`, `no-commit-to-branch` (blocks accidental commits to `main`)
- Apache 2.0 license-header check on every `.py` / `.ts` / `.tsx` / `.js` / `.jsx`

If a hook auto-fixes a file (for example, `ruff --fix` or `end-of-file-fixer`), the commit is rejected. Re-stage the modified files and commit again. Never bypass with `--no-verify`; if a hook is genuinely wrong, fix the config and open a follow-up PR.

## Branches

- Branch from `main`.
- Naming: lowercase, hyphens, descriptive but brief.
  - `phase-2-auto-classify`
  - `task-26645-multi-mcp`
  - `fix-prompt-escape-zero-width`
- Never push directly to `main`. Always via PR.

## Commits

- Lowercase, present tense, what changed. Max ~60 chars.
  - GOOD: `add patch_entity client with retry and circuit breaker`
  - BAD: `feat: implement comprehensive patch_entity integration with retry mechanism`
- NO conventional-commit prefixes (`feat:` / `chore:` / `refactor:`) unless the team agrees later. They add noise.
- Body after a blank line if context needed; summary stays short.

## Staging

NEVER `git add .` or `git add -A`. Always stage explicit filenames:

```bash
# Good — deliberate
git add src/copilot/clients/om_mcp.py src/copilot/services/agent.py tests/unit/test_om_mcp.py

# NEVER — blindly stages debug files, secrets, .env
git add .
git add -A
```

Run `git status` and `git diff --stat` first.

## Code conventions

Read [`CodePatterns.md`](CodePatterns.md) cover-to-cover before your first PR. Highlights:

- **Python**: pytest (not unittest), Pydantic v2, `mypy --strict`, `ruff` for everything else, `structlog` only (no `print()`, no bare `logging.*`).
- **TypeScript**: strict mode + `noUncheckedIndexedAccess`, NO `any`, NO `console.log` in production, NO MUI imports.
- **Comments**: only for complex business logic, non-obvious algorithms, public API docstrings, and `TODO`/`FIXME` with task IDs. NEVER `# Create user` before `create_user()`.
- **Three Laws of Implementation** in [`CLAUDE.md`](CLAUDE.md): layer separation, handle every error path, every external call has timeout + retry + circuit breaker.
- **The 5 Things AI Never Adds**: retry, circuit breaker, timeout, rate limit, structured errors. PR review enforces each one.

## License headers

Every new source file (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`) must start with the Apache 2.0 header. Template in [`LICENSE_HEADER.txt`](LICENSE_HEADER.txt). CI's `license-header-check` job blocks merge if any file is missing one.

## Testing

- Add tests in the same PR as the code change.
- Mock at boundaries (HTTP clients, third-party APIs), not internals.
- Test outcomes (API responses, observed state), not implementation (`verify(mock).method_called()`).
- `make test` must pass locally before opening the PR.

## PR process

1. Push your branch + open a PR using the [`PR template`](.github/PULL_REQUEST_TEMPLATE.md).
2. CI runs automatically (lint, type-check, unit tests, security scan, secret scan, UI build, path-guard).
3. Reviewer (@GunaPalanivel for now) walks the [`PR-Review/Checklist.md`](.idea/Plan/PR-Review/Checklist.md) — Architecture Integrity, Resilience, Observability, AI/ML Security gates.
4. Address comments, push fixes (don't squash mid-review unless asked).
5. Reviewer approves; you (or reviewer) squash-merge with a clean commit message.

## What NOT to import from OpenMetadata directly

We are STANDALONE. We do NOT depend on `openmetadata-spec` or `openmetadata-service` source. We connect to OpenMetadata via the official `data-ai-sdk` PyPI package. Do not add `from metadata.generated...` or `from metadata.ingestion...` imports without an ADR justifying why the public SDK is insufficient. See [`CodePatterns.md` §6](CodePatterns.md).

## Security

Found a vulnerability? Don't open a public issue — see [`SECURITY.md`](SECURITY.md) for the responsible disclosure flow.

## Internal planning docs

Most of `.idea/Plan/` is published in this repo as a strong signal of engineering process (ADRs, NFRs, threat model, runbook, etc.). A small subset is gitignored and stays internal — see `.gitignore` for the list. If you need to update a public planning doc, check the gitignore patterns first to make sure you're not editing a private file accidentally.

## Questions

Open an issue with the `question` label, or ping @GunaPalanivel.
