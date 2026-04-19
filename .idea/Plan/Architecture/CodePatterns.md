# CodePatterns.md (canonical source)

> Conventions for `openmetadata-mcp-agent` derived from OpenMetadata's own [CLAUDE.md](../../../CLAUDE.md). Any human contributor or AI agent working on the new repo must follow these patterns. The goal: a contributor moving between OM upstream and our repo feels at home in 30 seconds.
>
> **Distribution**: this file lives canonically here in `.idea/Plan/Architecture/CodePatterns.md`. The scaffold round drops a verbatim copy into `<openmetadata-mcp-agent>/CodePatterns.md` at the root of the new repo so it is the FIRST file every contributor reads after `README.md` + `CLAUDE.md`.

---

## 1. Comments policy (verbatim from OM CLAUDE.md)

- Do NOT add unnecessary comments. Write self-documenting code.
- NEVER add single-line comments that describe what the code obviously does.
- Only comment for:
  - Complex business logic that isn't obvious
  - Non-obvious algorithms or workarounds
  - Public API docstrings (Google-style for Python, JSDoc for TS)
  - `TODO`/`FIXME` with a task ID reference (e.g. `# TODO P2-04`)

Bad examples (NEVER do this):

- `# Create user` before `create_user()`
- `# Get client` before `client = OpenAI()`
- `# Verify entity is set` before `assert entity is not None`
- `# Lowercase the name` when the code already says `.lower()`

If the code needs a comment to be understood, refactor the code instead.

## 2. Python (mirrors OM `ingestion/` conventions)

### Test framework

- `pytest`, NOT `unittest`. Plain `assert x == y`, NOT `self.assertEqual`.
- Use pytest fixtures, NOT `setUp`/`tearDown`.
- Use `unittest.mock` (`MagicMock`, `patch`) — compatible with pytest.
- Test classes do NOT inherit from `TestCase` — plain classes prefixed `Test`.
- Replace `self.assertIsNone(x)` with `assert x is None`.
- Replace `self.assertIn("text", string)` with `assert "text" in string`.

### Type hints

- Required everywhere. Bare `dict`, `list`, `Any` need a justification comment.
- `mypy --strict` gates CI (per [Security/CIHardening.md](../Security/CIHardening.md)).
- `from __future__ import annotations` at the top of every module that uses forward refs.

### Pydantic

- v2 only. Use `BaseModel` with explicit field types and `Field(...)` for constraints.
- Mutate via `.model_copy(update={...})`. NEVER mutate fields in place.
- Note for any future imports from OM SDK: OM schema types like `ColumnName`, `EntityName`, `FullyQualifiedEntityName`, `UUID` are Pydantic `RootModel[str]` subclasses where `str()` returns `"root='value'"` instead of the raw value. If we ever depend on those, use `model_str()` from `metadata.ingestion.ometa.utils`, NOT manual `hasattr(x, "root")` / `str(x.root)` checks. (We do NOT currently import these; see §6 What NOT to import.)

### Async

- FastAPI routes are `async def`.
- All clients (OM MCP, OpenAI, GitHub MCP) are `async`.
- Never `await` inside a CPU-bound loop without yielding (use `asyncio.gather` for fan-out).

### Logging

- `structlog` only. NEVER `print()`. NEVER bare `logging.*`.
- Bind `request_id` via `structlog.contextvars` per [Project/NFRs.md §NFR-06](../Project/NFRs.md).
- NEVER log: API keys, JWTs, full prompts, full tool args containing user data. Use the redaction processor in `src/copilot/observability/redact.py` per [Security/SecretsHandling.md](../Security/SecretsHandling.md).

### Error handling

- Always raise typed exceptions (`McpUnavailable`, `LlmInvalidOutput`, `ToolNotAllowlisted`, etc.).
- Never raise bare `Exception` or `RuntimeError` from business logic.
- Catch at the API boundary; return the structured envelope per [Architecture/APIContract.md](./APIContract.md).
- No empty `except:` blocks. No bare `except Exception:` swallowing the error.

### Naming

- snake_case for functions, modules, variables. PascalCase for classes. UPPER_SNAKE for constants.
- Modules are nouns: `classifier.py`, `lineage_summarizer.py`, `om_mcp.py`.
- Functions are verbs: `classify_columns()`, `apply_tags()`, `is_valid()`.
- Booleans are question-form: `is_active`, `has_permission`, `can_retry`. NEVER `flag`, `status`, `check`.
- No single-letter variables except in short lambdas or loop indices.

### Imports

- Standard library → third-party → first-party → relative; one group per block, blank line between groups.
- Sorted alphabetically within each group (ruff handles this).
- No wildcard imports (`from foo import *`).
- No relative imports across more than one parent (`from ...foo import bar` is banned).

## 3. TypeScript / React (mirrors OM `openmetadata-ui` conventions)

### Strict mode

`tsconfig.json` MUST have:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### Type discipline (verbatim from OM CLAUDE.md)

- NEVER use `any` — always use proper types.
- Use `unknown` when the type is truly unknown and add type guards.
- NEVER use `as any` casts. If you must cast, add `// eslint-disable-next-line` with a justification comment.
- Import types from existing definitions (`RJSFSchema` from `@rjsf/utils`, etc.).

### React

- Functional components with hooks. NO class components.
- One component per file. File name = component name (`ChatMessage.tsx`).
- Props typed via `interface ChatMessageProps`. No anonymous types.
- For our small repo: simpler `ChatMessage.tsx` (instead of OM's `ChatMessage.component.tsx` + `ChatMessage.interface.ts` split — which makes sense for OM's 1000+ component scale but is overhead for ours).
- Use `useTranslation` only if/when we add i18n (out of scope for v1).
- `useNavigate` from `react-router-dom`, never direct history manipulation.

### Styling

- NO MUI imports. NO `@emotion`. (Mirrors OM's active migration AWAY from MUI.)
- OM brand: `#7147E8` primary, Inter font, dark mode default — verified in [openmetadata-ui/.../variables.less](../../../openmetadata-ui/src/main/resources/ui/src/styles/variables.less).
- CSS variables for design tokens in `ui/src/styles/tokens.css`.

### Console

- NEVER `console.log` / `warn` / `error` / `info` / `debug` in production code. ESLint `no-console` enforced.
- Use a logger or remove. For client-side logging, swallow until we add Sentry-style telemetry.

### Tests

- Use `it()` consistently — don't mix `test()` and `it()`.
- Blank lines around `describe`, `it`, `beforeEach`.
- NEVER `.only` on tests — blocks the rest of the suite in CI.
- Web-first assertions in Playwright (`expect(locator).toBeVisible()`), NOT `waitForSelector`.
- No `page.pause()` in committed code.
- No `{ force: true }` — fix the locator instead.

### Markdown rendering

- `react-markdown` + `rehype-sanitize`.
- NEVER `dangerouslySetInnerHTML`.

### Imports order (per OM)

1. External libraries (React, etc.)
2. Internal absolute imports (`generated/`, `constants/`, `hooks/`, etc.)
3. Relative imports for utilities and components
4. Asset imports (SVGs, styles)
5. Type imports grouped separately when needed

Run the equivalent of OM's `yarn organize-imports:cli` (we use `eslint-plugin-import`).

## 4. Git hygiene (mirrors OM)

### Staging — NEVER `git add .` or `git add -A`

```bash
# WRONG — stages everything including .env, debug files, secrets
git add .
git add -A
git add --all

# RIGHT — explicit filenames only
git add src/copilot/clients/om_mcp.py src/copilot/services/agent.py
```

Always check `git status` and `git diff --stat` before staging.

### Commit messages — write like a human, not an AI

```bash
# RIGHT — sounds like a real engineer
git commit -m "add patch_entity client with retry and circuit breaker"
git commit -m "wire up fastapi routes for chat and confirm"
git commit -m "fix prompt injection escape on column descriptions"

# WRONG — AI-generated, robotic, conventional-commit-prefixed
git commit -m "feat: implement comprehensive patch_entity integration with retry mechanism"
git commit -m "chore(P1): final integration validation — all gates pass"
git commit -m "refactor: implement multi-component reward calculator with dense per-step signal"
```

Rules (from OM CLAUDE.md):

- Lowercase, no period at end
- Max ~60 chars on the summary line; be specific about what changed
- NO `feat:` / `chore:` / `refactor:` conventional-commit prefixes
- Body after a blank line if context needed; summary stays short

### Branch naming

- lowercase, hyphens, descriptive but brief
- `phase-2-auto-classify`, `task-26645-multi-mcp`, `fix-prompt-escape`

## 5. License headers

- Every source file (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`) starts with the Apache 2.0 header.
- Header text in `LICENSE_HEADER.txt` at the repo root.
- `make license-header-check` verifies; CI fails if missing.
- For a new file, use `# Copyright 2026 Collate. Licensed under the Apache License, Version 2.0 (the "License");` header (Python comment) or the `/* */` block version for TS.

## 6. What NOT to import from OpenMetadata directly

We are a STANDALONE repo. We do NOT depend on `openmetadata-spec`, `openmetadata-service`, or `ingestion/` source code. We connect to OM via:

- `data-ai-sdk` PyPI package (the official Python SDK; mirrors OM's MCP server contract — see [DataFindings/ExistingMCPAudit.md §AI SDK Coverage](../DataFindings/ExistingMCPAudit.md))
- HTTP REST + JSON-RPC 2.0 to a running OM instance
- We do NOT `from metadata.generated...` or `from metadata.ingestion...`

Why:

- Independent deploy: we ship as a thin agent, not as part of the OM monorepo
- Avoids OM's heavyweight install during the 6-day hackathon timeline
- Forces us to use only the public, supported MCP surface — which is also what judges score on (Best Use of OpenMetadata)

If a contributor proposes adding `openmetadata-ingestion` or any `metadata.*` import, the PR is rejected unless the proposal includes an ADR explaining why the public SDK is insufficient. See [PR-Review/Checklist.md](../PR-Review/Checklist.md).

## 7. Method/function size (mirrors OM Java standards, ported to Python/TS)

OM's Java standards say "methods must be 15 lines or fewer". Same idea applies to Python and TypeScript:

- Functions are < 50 lines (refactor if longer; OM's 15-line bar is for Java which is verbose; Python's expressiveness allows ~50 LoC before it gets unreadable).
- Maximum 3 levels of nesting. Use early returns:

```python
# WRONG: deeply nested
def process(entity):
    if entity is not None:
        if entity.is_active():
            if has_permission(entity):
                do_thing(entity)

# RIGHT: early returns, flat
def process(entity):
    if entity is None:
        return
    if not entity.is_active():
        return
    if not has_permission(entity):
        return
    do_thing(entity)
```

- Maximum 5 parameters. Introduce a Pydantic model or builder for more.
- Each function does one thing. If you can describe what it does using "and" or "then", split it.

## 8. Magic strings (mirrors OM)

- NEVER use raw string literals in `.equals()`, `.contains()`, or `match` cases — define a constant or use an enum.
- If the same string appears in more than one place, it must be a named constant.
- One definition, one location.

```python
# WRONG: magic strings scattered everywhere
if task_status == "Open": ...
if config.resources[0] == "all": ...

# RIGHT: enum / constant
from enum import StrEnum

class TaskStatus(StrEnum):
    OPEN = "Open"
    CLOSED = "Closed"

RESOURCE_ALL = "all"

if task_status is TaskStatus.OPEN: ...
if config.resources[0] == RESOURCE_ALL: ...
```

The `MCPTool` `Literal[...]` type in [Architecture/DataModel.md](./DataModel.md) is the canonical example we already follow.

## 9. No code duplication

- If the same logic exists in two places, extract to a shared function or service.
- Near-identical code paths should share a common implementation with parameterized variations.
- Copy-pasted blocks within the same file get extracted into a parameterized helper.

## 10. Class size

- Modules under 500 lines. Over 1000 lines is a design problem.
- If a service module grows large, look for clusters of functions that operate on the same subset of state — extract them into a focused submodule.
- Routes (`api/`) are thin orchestrators. Business logic lives in `services/`. Data access lives in `clients/`. Per [Architecture/CodingStandards.md §Three Laws of Implementation](./CodingStandards.md).

## 11. Common bug patterns to avoid

From OM CLAUDE.md, ported to Python:

- `==` instead of `is` for `None` comparisons → use `x is None`, not `x == None`
- Mutating a default mutable argument (`def foo(x=[]):` is a bug)
- String concatenation inside loops → use `"".join(parts)` or f-strings
- Calling `.size() == 0` style — use `not collection` or `len(collection) == 0`
- `dict.get(key)` swallowing the `None` case silently when you needed a `KeyError`
- `try: ... except: pass` swallowing exceptions silently
- F-string interpolation of secrets (`f"Bearer {settings.openai_api_key}"` — ALWAYS use `.get_secret_value()` and never log the result; per [Security/SecretsHandling.md](../Security/SecretsHandling.md))
- Unhandled `await` in async functions
- Unbounded recursion (LangGraph state machines must have an explicit max_iterations)

## 12. Testing philosophy (verbatim from OM CLAUDE.md)

- Test real behavior, not mock wiring. If a test mocks 3+ classes just to verify a method call, it's testing the wrong thing.
- Prefer integration tests over heavily-mocked unit tests.
- Mocks are for boundaries (HTTP clients, third-party APIs), NOT internals. Mock OM MCP responses; do NOT mock our own service classes.
- A test that mocks everything proves nothing.
- Ask: "what breaks if this test passes but the code is wrong?" If "nothing", delete the test.
- Test the outcome (API responses, observed state), not the implementation (`verify(mock).method_called()`).

## 13. Documentation philosophy (mirrors OM's `docs/` pattern)

- Docs in `docs/` (this repo), planning in `.idea/Plan/` (workspace-only, never pushed).
- OSS structure: `README.md`, `docs/getting-started.md`, `docs/architecture.md`, `docs/api.md`, `docs/runbook.md`, `docs/contributing.md`.
- Write docs as features land, not before, not all at once.
- Write for an external user who cloned the repo cold — not for yourselves.
- Internal planning goes in `.idea/Plan/Architecture/`, not `docs/`.

## 14. Reading order for AI agents working on this repo

When unsure, read in this order:

1. [README.md](../../README.md) — what is this project
2. [CLAUDE.md](../../CLAUDE.md) — top-level architecture contract (Three Laws, the 5 Things, layering, non-negotiables)
3. **This file** (`CodePatterns.md`) — language/framework conventions
4. [CONTRIBUTING.md](../../CONTRIBUTING.md) — workflow (branches, PRs, reviews)
5. The relevant module's docstring
6. The matching `.idea/Plan/` doc (Architecture/, Security/, FeatureDev/, etc.)
7. If still unsure, ask in the issue thread before coding

## Compatibility with OpenMetadata upstream

Our repo is a STANDALONE Python+React project. We do NOT mirror OM's full multi-module Maven+Webpack monorepo structure (that would require Java + Yarn + Webpack + Flyway + every OM connector — pointless overhead for our scope). What we DO mirror, so OM contributors feel at home:

| OM upstream                                        | Our repo equivalent                                                                                            |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `openmetadata-service/` (Java backend)             | `src/copilot/api/` + `src/copilot/services/` (Python backend, layered same way)                                |
| `openmetadata-ui/src/main/resources/ui/` (React)   | `ui/` (React 18 + Vite + TS, same conventions)                                                                 |
| `ingestion/` (Python framework)                    | `src/copilot/clients/` + `src/copilot/models/` (Python data layer)                                             |
| `openmetadata-spec/.../json/schema/` (JSON Schema) | `src/copilot/models/` (Pydantic v2 — analogous role of "schema source of truth")                               |
| `bootstrap/sql/` (Flyway migrations)               | N/A in v1 (no DB)                                                                                              |
| `docker/` (compose files)                          | `infrastructure/` (compose files)                                                                              |
| `conf/openmetadata.yaml`                           | `.env` + `src/copilot/config/settings.py` (Pydantic Settings)                                                  |
| `Makefile` (top-level + `ingestion/Makefile`)      | `Makefile` (single, with OM-named targets like `make install_dev_env`, `make py_format`, `make static-checks`) |
| `.github/workflows/*.yml`                          | `.github/workflows/ci.yml`                                                                                     |
| `CLAUDE.md` (workspace AI guidance)                | `CLAUDE.md` (repo-root AI guidance)                                                                            |
| `DEVELOPER.md`                                     | `CONTRIBUTING.md` (combines OM's developer-onboarding + contributor-flow into one)                             |

A contributor cloning our repo who has previously worked on OM upstream should recognize: layered backend, Pydantic-as-schema, Makefile workflow, GitHub Actions CI, Apache 2.0 license, no MUI, no `console.log`, structured logging, conventional Python testing — all the same conventions, scoped down to our smaller surface.

## Maintenance

This file is the canonical source. The repo-root copy is generated from this file during scaffold and during any subsequent regen. If you edit one without the other, run a manual diff before merging — the two should stay byte-identical except for the top frontmatter line ("canonical source" vs "generated copy").
