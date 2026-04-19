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

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    openai_timeout_seconds: float = Field(default=8.0, gt=0)
    openai_max_retries: int = Field(default=2, ge=0)

    # ---------- Logging ----------
    log_level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance.

    Cached so .env is read once per process. Tests can override by calling
    get_settings.cache_clear() between cases.
    """
    return Settings()
