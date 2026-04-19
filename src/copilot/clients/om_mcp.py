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
"""OpenMetadata MCP client - thin wrapper around `data-ai-sdk` with circuit breaker.

Per .idea/Plan/Project/NFRs.md "The 5 Things AI Never Adds":
  - timeout: 5.0s connect, 5.0s read (settings.om_timeout_seconds)
  - retry: 3 attempts, exponential backoff with jitter
  - circuit breaker: open after 5 consecutive failures, 30s cooldown
  - structured error: maps SDK errors to McpUnavailable / McpAuthFailed

P1-03 task: implement search_metadata round-trip and verify against a running
local OM Docker. This file is the scaffold; functional bodies pending.
"""

from __future__ import annotations

from typing import Any

import pybreaker

from copilot.config import get_settings
from copilot.middleware.error_envelope import McpUnavailable  # McpAuthFailed used in P1-03 impl
from copilot.observability import get_logger

log = get_logger(__name__)

_settings = get_settings()

# Circuit breaker per NFRs.md: open after 5 consecutive failures, 30s cooldown.
om_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="om_mcp",
)


# TODO P1-03: implement actual data-ai-sdk wiring.
# Pseudocode for the implementation:
#
#   from ai_sdk import AISdk, AISdkConfig
#   from ai_sdk.exceptions import MCPError
#
#   _client = AISdk.from_config(AISdkConfig(
#       host=_settings.ai_sdk_host,
#       token=_settings.ai_sdk_token.get_secret_value(),
#       timeout=_settings.om_timeout_seconds,
#       max_retries=_settings.om_max_retries,
#   ))
#
#   @om_breaker
#   async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
#       log.info("om.call_tool.start", tool=name)
#       try:
#           result = _client.mcp.call_tool(name, arguments)
#       except MCPError as exc:
#           if exc.status_code == 401:
#               raise McpAuthFailed from exc
#           raise McpUnavailable from exc
#       log.info("om.call_tool.complete", tool=name, ok=result.success)
#       if not result.success:
#           raise McpUnavailable(result.error or "unknown")
#       return result.data or {}


async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call an MCP tool by name. Stubbed in Phase 1; implement in P1-03."""
    log.warning("om.call_tool.not_implemented", tool=name)
    raise McpUnavailable("om_mcp.call_tool not implemented yet (P1-03)")


async def list_tools() -> list[str]:
    """Refresh the list of tools the OpenMetadata MCP server exposes.

    Cached every 60s in production; called once at startup to populate the
    allowlist intersection per Module G defense Layer 4.
    """
    log.warning("om.list_tools.not_implemented")
    raise McpUnavailable("om_mcp.list_tools not implemented yet (P1-03)")
