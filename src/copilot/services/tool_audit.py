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
"""Shared tool argument redaction + result summaries for audit logs."""

from __future__ import annotations

import json
from typing import Any


def redact_tool_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Redact potentially sensitive values from tool arguments for audit logs."""
    redacted: dict[str, Any] = {}
    sensitive_keys = {"token", "password", "secret", "api_key", "jwt"}
    for key, value in arguments.items():
        if key.lower() in sensitive_keys:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, str) and len(value) > 200:
            redacted[key] = value[:200] + "...[truncated]"
        else:
            redacted[key] = value
    return redacted


def summarize_tool_result(result: dict[str, Any]) -> str:
    """Create a brief summary of a tool call result for the audit log."""
    summary = json.dumps(result, default=str)
    if len(summary) > 500:
        return summary[:497] + "..."
    return summary
