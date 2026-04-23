#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Pydantic Settings - single source of truth for runtime config.

Per .idea/Plan/Security/SecretsHandling.md and .idea/Plan/Security/ThreatModel.md:
- All three secrets are SecretStr (never accidentally stringified into logs).
- host defaults to 127.0.0.1 (SC-1: loopback-only ingress in v1).
- All resilience knobs from .idea/Plan/Project/NFRs.md exposed.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Substrings that indicate the user copied .env.example without replacing secrets.
_ENV_PLACEHOLDER_MARKERS = (
    "paste-your",
    "paste your",
    "changeme",
    "example-token",
    "your-key-here",
)

# Example GitHub PAT lines sometimes copied into .env for Phase 1-2 — treat as unset.
_GITHUB_TOKEN_TEMPLATE_MARKERS = (
    "ghp_your",
    "github_pat_xxxx",
    "paste-your",
    "your_pat_here",
    "your_fine_grained",
)


def _normalize_env_secret(value: str) -> str:
    """Strip BOM / whitespace / wrapping quotes often introduced by editors on Windows."""
    v = value.strip()
    if v.startswith("\ufeff"):
        v = v[1:].strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in {'"', "'"}:
        v = v[1:-1].strip()
    return v


def _is_placeholder_secret(normalized_value: str) -> bool:
    v = normalized_value.lower()
    if not v:
        return True
    return any(marker in v for marker in _ENV_PLACEHOLDER_MARKERS) or (
        v.startswith("sk-paste") or v.startswith("sk-fake")
    )


def _github_pat_looks_like_template(normalized_lower: str) -> bool:
    return any(marker in normalized_lower for marker in _GITHUB_TOKEN_TEMPLATE_MARKERS)


class Settings(BaseSettings):
    """Runtime configuration loaded from environment + .env file.

    Use get_settings() (cached singleton) instead of constructing directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Secrets (SC-2: SecretStr, never logged) ----------
    ai_sdk_token: SecretStr = Field(
        default=SecretStr(""),
        description="OpenMetadata Bot JWT for MCP calls",
    )
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key for the LLM",
    )
    github_token: SecretStr | None = Field(
        default=None,
        description="GitHub PAT for the multi-MCP demo (Phase 3 only)",
    )

    @field_validator("github_token", mode="before")
    @classmethod
    def _github_token_coerce(cls, value: object) -> object:
        """Empty, template PATs, or ``GITHUB_TOKEN=`` mean GitHub MCP is off (Phase 1-2)."""
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            return value
        cleaned = _normalize_env_secret(value)
        if not cleaned:
            return None
        if _github_pat_looks_like_template(cleaned.lower()):
            return None
        return cleaned

    # ---------- Public config ----------
    ai_sdk_host: str = Field(
        default="http://localhost:8585",
        description="OpenMetadata server URL",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model name (per ADR-03)",
    )

    # ---------- Network bind (SC-1: NEVER 0.0.0.0 in v1) ----------
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)

    # ---------- Resilience (per .idea/Plan/Project/NFRs.md) ----------
    om_timeout_seconds: float = Field(default=5.0, gt=0)
    om_max_retries: int = Field(default=3, ge=0)
    om_mcp_http_path: str = Field(
        default="/mcp",
        description=(
            "HTTP path for data-ai-sdk JSON-RPC MCP calls (must start with /). "
            "Official default is /mcp; some OM builds return 405 on POST /mcp — "
            "set OM_MCP_HTTP_PATH to the path your server documents."
        ),
    )

    @field_validator("om_mcp_http_path", mode="after")
    @classmethod
    def _normalize_om_mcp_http_path(cls, v: str) -> str:
        p = (v or "").strip()
        if not p:
            return "/mcp"
        if not p.startswith("/"):
            return "/" + p
        return p

    openai_timeout_seconds: float = Field(default=8.0, gt=0)
    openai_max_retries: int = Field(default=2, ge=0)

    # ---------- Drift polling ----------
    drift_poll_interval_seconds: float = Field(
        default=60.0,
        gt=0,
        description="Seconds between background drift scans",
    )

    # ---------- Logging ----------
    log_level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")


def assert_runtime_env_ready(settings: Settings) -> None:
    """Fail fast if required secrets are missing or still template values.

    Skipped automatically under pytest (``PYTEST_VERSION`` is set). Override with
    ``COPILOT_SKIP_ENV_VALIDATION=1`` only for special non-pytest tooling.
    """
    if os.environ.get("COPILOT_SKIP_ENV_VALIDATION", "").lower() in ("1", "true", "yes"):
        return
    if os.environ.get("PYTEST_VERSION"):
        return

    problems: list[str] = []

    host = (settings.ai_sdk_host or "").strip()
    if not host:
        problems.append("AI_SDK_HOST is empty")

    om_token = _normalize_env_secret(settings.ai_sdk_token.get_secret_value())
    if _is_placeholder_secret(om_token):
        problems.append(
            "AI_SDK_TOKEN is missing or still a placeholder (replace with a real Bot JWT from OM)"
        )

    oai_key = _normalize_env_secret(settings.openai_api_key.get_secret_value())
    if _is_placeholder_secret(oai_key):
        problems.append(
            "OPENAI_API_KEY is missing or still a placeholder (use a real key from platform.openai.com)"
        )
    elif not re.match(r"^sk-[A-Za-z0-9_-]{8,}$", oai_key):
        problems.append(
            "OPENAI_API_KEY does not look like a valid OpenAI secret key (expected sk-...)"
        )

    if problems:
        msg = (
            "Environment is not ready to run the agent backend:\n  - "
            + "\n  - ".join(problems)
            + "\n\nFix: copy .env.example to .env and set real values, or run `make setup` then edit .env. "
            "Never commit secrets. For tests only, set COPILOT_SKIP_ENV_VALIDATION=1."
        )
        raise RuntimeError(msg)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance.

    Cached so .env is read once per process. Tests can override by calling
    get_settings.cache_clear() between cases.
    """
    return Settings()
