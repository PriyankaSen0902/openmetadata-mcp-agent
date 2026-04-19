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
"""Structlog processor that strips known secret values from log entries.

Defense-in-depth per .idea/Plan/Security/SecretsHandling.md SC-2 + SC-8.
Even with SecretStr discipline, an accidental f-string interpolation
(`f"Bearer {secret.get_secret_value()}"`) could leak a token into a log line.
This processor scans every string field in every log entry and replaces any
known-secret substring with [REDACTED].
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Strings shorter than this are not considered "secret-like" - avoids
# false-positive redactions of short config strings.
MIN_SECRET_LENGTH = 16

REDACTED_PLACEHOLDER = "[REDACTED]"


def make_redaction_processor(known_secrets: list[str]) -> Callable[..., dict[str, Any]]:
    """Build a structlog processor that redacts the given secret values.

    Args:
        known_secrets: list of secret values to scrub. Empty strings + values
            shorter than MIN_SECRET_LENGTH are filtered out (would cause
            false-positive redactions).

    Returns:
        A structlog processor compatible with structlog.configure(processors=...).
    """
    secret_set = {s for s in known_secrets if s and len(s) >= MIN_SECRET_LENGTH}

    def redact(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        if not secret_set:
            return event_dict
        for key, value in list(event_dict.items()):
            if isinstance(value, str):
                redacted = value
                for secret in secret_set:
                    if secret in redacted:
                        redacted = redacted.replace(secret, REDACTED_PLACEHOLDER)
                if redacted is not value:
                    event_dict[key] = redacted
        return event_dict

    return redact
