# Contributing — Quick Reference

The full contributor guide lives at [`CONTRIBUTING.md`](../CONTRIBUTING.md) at the repo root. This page is a quick lookup for OpenMetadata-pattern checks.

## Apache 2.0 license header

Every new source file (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`) must start with the Apache 2.0 header from [`LICENSE_HEADER.txt`](../LICENSE_HEADER.txt). CI's `license-header-check` blocks merge if any file is missing one.

Verify locally:

```bash
make license-header-check
# Or directly:
python scripts/check_license_headers.py
```

## OpenMetadata-aliased Make targets

Familiar to OpenMetadata upstream contributors:

| Our target | Equivalent at OpenMetadata upstream |
|------------|--------------------------------------|
| `make install_dev_env` | `cd ingestion && make install_dev_env` |
| `make py_format` | `make py_format` (we use `ruff format` instead of `black + isort + pycln`) |
| `make static-checks` | `make static-checks` (we use `mypy --strict` instead of `basedpyright`) |
| `make lint` | `make lint` |
| `make test` | `make unit_ingestion_dev_env` (and integration variants) |
| `make ci-local` | full CI emulation locally (lint + types + tests + security scan + UI build) |

## What NOT to import from OpenMetadata directly

We are STANDALONE. NO `from metadata.generated...` or `from metadata.ingestion...`. We connect to OpenMetadata via the `data-ai-sdk` PyPI package. Adding any other OpenMetadata import requires an ADR justifying why the public SDK is insufficient.

## Code conventions

See [`CodePatterns.md`](../CodePatterns.md). Highlights specific to OpenMetadata-style:

- **Comments policy**: only complex business logic / non-obvious algorithms / public docstrings / TODO with task ID. NEVER `# Create user` before `create_user()`.
- **Python**: pytest (not unittest), Pydantic v2, mypy --strict, structlog (no `print()`).
- **TypeScript**: strict mode, no `any`, no `console.log` in production code, no MUI imports.
- **Method/function size**: <50 lines Python (OpenMetadata says 15 for Java), max 3 nesting levels, max 5 parameters.
- **No magic strings**: extract enums or constants; one definition, one location.
- **No code duplication**: extract shared helpers.
- **Class/module size**: under 500 lines.

## Git hygiene (per OpenMetadata's CLAUDE.md Git section)

- NEVER `git add .` — explicit filenames only.
- Lowercase commit messages, present tense, what changed (NO `feat:` / `chore:` prefixes).
- Branch names: `phase-2-auto-classify`, `task-26645-multi-mcp`, `fix-prompt-escape`.

## Testing philosophy (verbatim from OpenMetadata's CLAUDE.md)

- Test real behavior, not mock wiring. If a test mocks 3+ classes just to verify a method call, it's testing the wrong thing.
- Prefer integration tests over heavily-mocked unit tests.
- Mocks are for boundaries (HTTP clients, third-party APIs), NOT internals.
- A test that mocks everything proves nothing.
