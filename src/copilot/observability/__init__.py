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
"""Observability bootstrap: structlog (JSON) + Prometheus + redaction processor.

Per .idea/Plan/Project/NFRs.md NFR-06 and .idea/Plan/Architecture/Overview.md
Observability Subsystem: structlog with redaction processor wired in,
Prometheus metrics exposed via observability.metrics module.

Call configure_observability() ONCE at app startup (e.g. in api/main.py
lifespan handler). After that, get_logger() returns a request_id-aware logger
suitable for any module.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from copilot.config import get_settings
from copilot.observability.redact import make_redaction_processor


def configure_observability() -> None:
    """Configure structlog + stdlib logging once at process startup.

    Idempotent - safe to call multiple times (e.g. in tests). Reads
    settings.log_level and the three secrets to wire the redaction processor.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    secret_values: list[str] = []
    if settings.ai_sdk_token.get_secret_value():
        secret_values.append(settings.ai_sdk_token.get_secret_value())
    if settings.openai_api_key.get_secret_value():
        secret_values.append(settings.openai_api_key.get_secret_value())
    if settings.github_token is not None and settings.github_token.get_secret_value():
        secret_values.append(settings.github_token.get_secret_value())

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            make_redaction_processor(secret_values),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger. Call after configure_observability()."""
    return structlog.get_logger(name)


__all__ = ["configure_observability", "get_logger"]
