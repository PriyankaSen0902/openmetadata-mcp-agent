# Secrets Handling

> Per [security-vulnerability-auditor SKILL §Module D](../../agents/security-vulnerability-auditor/SKILL.md). Three secrets, one policy each. Enforced by code (`pydantic_settings.SecretStr`), runtime (structlog redaction), and CI (`bandit` + `gitleaks`).

## The three secrets

| Name             | Purpose                                         | Where used                             | Sensitivity                                             |
| ---------------- | ----------------------------------------------- | -------------------------------------- | ------------------------------------------------------- |
| `AI_SDK_TOKEN`   | OM Bot JWT for MCP calls                        | `clients/om_mcp.py` (every tool call)  | High — grants bot-user write access to the catalog      |
| `OPENAI_API_KEY` | OpenAI API access for the LLM                   | `clients/openai_client.py`             | High — grants spend on our paid OpenAI account          |
| `GITHUB_TOKEN`   | GitHub PAT for the GitHub MCP create-issue flow | `clients/github_mcp.py` (Phase 3 only) | Medium — scoped to single repo with `issues:write` only |

## Storage

| Layer                     | Mechanism                                                                   |
| ------------------------- | --------------------------------------------------------------------------- |
| Source code               | `.env.example` (template, no real values, checked in)                       |
| Local dev                 | `.env` (real values, NEVER checked in; `.env` in `.gitignore`; `chmod 600`) |
| CI                        | GitHub Actions Secrets (encrypted at rest by GitHub; never echoed)          |
| Demo machine              | `.env` file with restricted permissions; rotated 24h before demo            |
| Production (out of scope) | Vault / AWS Secrets Manager / 1Password Connect                             |

## Loading

```python
# src/copilot/config/settings.py
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Three secrets — typed as SecretStr so __repr__/__str__ never leaks the value
    ai_sdk_token: SecretStr
    openai_api_key: SecretStr
    github_token: SecretStr | None = None  # Phase 3 only

    # Public config (not secret, fine to log)
    ai_sdk_host: str = "http://localhost:8585"
    openai_model: str = "gpt-4o-mini"
    host: str = "127.0.0.1"  # SC-1: loopback only
    port: int = 8000

    # Resilience knobs
    om_timeout_seconds: float = 5.0
    om_max_retries: int = 3
    openai_timeout_seconds: float = 8.0
    openai_max_retries: int = 2

settings = Settings()  # singleton, loaded at import time
```

## Use

```python
# WRONG — leaks the secret in logs/stack traces if anything happens
headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

# WRONG — same problem; SecretStr.__str__ is "**********" but the f-string would force unwrap
headers = {"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"}
log.info("calling openai", headers=headers)  # leaks!

# RIGHT — extract only at call site, never log
def get_openai_client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )

# Logging the call:
log.info("openai.call", model=settings.openai_model, request_id=request_id)
```

## Logging redaction processor

Even with `SecretStr` discipline, defense in depth: structlog has a custom processor that strips known secret values from any log line.

```python
# src/copilot/observability/redact.py
from structlog.processors import EventRenamer
from typing import Any

def make_redaction_processor(known_secrets: list[str]):
    """
    structlog processor that finds any known-secret string in event values and
    replaces it with [REDACTED]. Defense against accidental f-string interpolation.
    """
    secret_set = {s for s in known_secrets if s and len(s) >= 16}  # don't redact short non-secrets

    def redact(logger, method_name, event_dict: dict[str, Any]) -> dict[str, Any]:
        for key, value in list(event_dict.items()):
            if isinstance(value, str):
                for secret in secret_set:
                    if secret in value:
                        event_dict[key] = value.replace(secret, "[REDACTED]")
        return event_dict

    return redact

# Wired up in observability/__init__.py:
import structlog
from .redact import make_redaction_processor
from copilot.config import settings

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        make_redaction_processor([
            settings.ai_sdk_token.get_secret_value(),
            settings.openai_api_key.get_secret_value(),
            (settings.github_token.get_secret_value() if settings.github_token else None),
        ]),
        structlog.processors.JSONRenderer(),
    ],
)
```

## Error envelope discipline

Per [APIContract.md](../Architecture/APIContract.md), the error envelope NEVER includes:

- Authorization headers (full or redacted form)
- File system paths (`/Users/...`, `C:\Users\...` — leaks dev environment)
- Raw exception strings (may contain SQL, secrets, internal pointers)
- Full prompts sent to the LLM (may echo a recent attacker injection)
- Full tool call arguments containing user-supplied content

Enforced by `middleware/error_envelope.py`:

```python
# src/copilot/middleware/error_envelope.py
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

SAFE_ERROR_CODES = {
    "validation_failed", "tool_not_allowlisted", "confirmation_required",
    "confirmation_expired", "om_unavailable", "om_auth_failed",
    "llm_unavailable", "llm_invalid_output", "llm_token_budget_exceeded",
    "rate_limited", "internal_error",
}

async def envelope_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = request.state.request_id  # set by request_id middleware

    code = getattr(exc, "envelope_code", "internal_error")
    if code not in SAFE_ERROR_CODES:
        code = "internal_error"

    # Use the canonical mapped message, NEVER str(exc)
    message = SAFE_MESSAGES[code]
    status_code = STATUS_CODES[code]

    log.error("api.error", code=code, request_id=request_id, exc_info=True)  # full stack -> log only

    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "request_id": str(request_id),
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )
```

## Rotation

| Secret           | Rotation policy                                                                                                      | Owner   |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- | ------- |
| `AI_SDK_TOKEN`   | Regenerate from OM UI Settings → Bots → ingestion-bot before each demo (24h before is acceptable); set 30-day expiry | OMH-ATL |
| `OPENAI_API_KEY` | Two accounts; rotate primary if quota hits; new key for production-equivalent demo                                   | OMH-GSA |
| `GITHUB_TOKEN`   | Fine-grained PAT scoped to single demo repo, `issues:write` only, 30-day expiry; revoke after submission             | OMH-GSA |

Rotation procedure documented in [Project/Runbook.md §Failure mode 2](../Project/Runbook.md).

## CI secrets handling

Per [CIHardening.md](./CIHardening.md):

- GitHub Actions secrets stored encrypted at rest
- `OPENAI_API_KEY` referenced as `${{ secrets.OPENAI_API_KEY }}` in workflows
- Never exposed to PRs from forks (job-level `if: github.event.pull_request.head.repo.full_name == github.repository`)
- `bandit` + `gitleaks` scan every PR for accidental commits

## .env.example template

The repo will contain `.env.example` with this exact content (placeholder values only):

```bash
# OpenMetadata MCP server (data-ai-sdk reads these directly)
AI_SDK_HOST=http://localhost:8585
AI_SDK_TOKEN=paste-your-bot-jwt-here

# OpenAI (LLM provider)
OPENAI_API_KEY=sk-paste-your-key-here
OPENAI_MODEL=gpt-4o-mini

# GitHub MCP (Phase 3 only — leave blank for v1)
GITHUB_TOKEN=

# Resilience knobs (defaults are fine; override only for testing)
OM_TIMEOUT_SECONDS=5.0
OM_MAX_RETRIES=3
OPENAI_TIMEOUT_SECONDS=8.0
OPENAI_MAX_RETRIES=2

# FastAPI bind (DO NOT change to 0.0.0.0 in v1; see Security/ThreatModel.md SC-1)
HOST=127.0.0.1
PORT=8000
```

`.env` is in `.gitignore`. `.env.example` is the only file checked in.

## Verification checklist (run at each Phase Exit Gate)

```
[ ] git log --all --source -- .env returns no commits
[ ] gitleaks scan returns 0 findings
[ ] bandit -r src/ returns 0 findings (or all are tagged --no-sec with justification)
[ ] grep -rn "OPENAI_API_KEY\|AI_SDK_TOKEN\|GITHUB_TOKEN" src/ shows no string literals (only env access)
[ ] Manually grep logs/agent.log for secret values: rg "$OPENAI_API_KEY" logs/ returns nothing
[ ] Production demo .env has chmod 600 (Unix) or restricted ACL (Windows)
```
