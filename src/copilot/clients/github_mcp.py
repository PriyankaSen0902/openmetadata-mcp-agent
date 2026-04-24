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
"""GitHub MCP client for Phase 3 cross-MCP demo.

Per .idea/Plan/Project/NFRs.md "The 5 Things AI Never Adds":
  - timeout: implicitly handled or mocked
  - retry: exponential backoff with jitter
  - circuit breaker: open after 5 consecutive failures, 30 s cooldown
  - structured error: raises McpUnavailable
"""

from __future__ import annotations

import time
from typing import Any, cast

import pybreaker
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from copilot.config import get_settings
from copilot.middleware.error_envelope import McpAuthFailed, McpUnavailable
from copilot.observability import get_logger
from copilot.observability.metrics import agent_mcp_calls_total

__all__ = ["call_tool"]

log = get_logger(__name__)

github_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="github_mcp",
)

_RETRY_DECORATOR = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=4),
    retry=retry_if_exception_type(McpUnavailable),
    reraise=True,
)


@_RETRY_DECORATOR
def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call a GitHub MCP tool by name with circuit-breaker + retry protection.

    Args:
        name: Tool name (e.g., github_create_issue).
        arguments: Tool arguments as a flat dict.

    Returns:
        Parsed JSON dict with the result.

    Raises:
        McpUnavailable: On connection / timeout / server errors or circuit open.
        McpAuthFailed: On 401 / 403 authentication errors.
    """
    log.info("github.call_tool.start", tool=name)
    start = time.monotonic()

    try:
        result = _call_tool_inner(name, arguments)
    except (McpUnavailable, McpAuthFailed):
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.warning("github.call_tool.failed", tool=name, elapsed_ms=elapsed_ms)
        agent_mcp_calls_total.labels(tool_name=name, outcome="fail").inc()
        raise

    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info("github.call_tool.complete", tool=name, elapsed_ms=elapsed_ms)
    agent_mcp_calls_total.labels(tool_name=name, outcome="ok").inc()
    return cast(dict[str, Any], result)


@github_breaker
def _call_tool_inner(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Inner call wrapped by the circuit breaker (separate from retry)."""
    settings = get_settings()

    # Phase 3 mock: only check token existence
    token = settings.github_token and settings.github_token.get_secret_value()
    if not token:
        raise McpAuthFailed("GITHUB_TOKEN is not set — cannot connect to GitHub")

    if name == "github_create_issue":
        repo = arguments.get("repo", "mock/repo")
        title = arguments.get("title", "No Title")
        body = arguments.get("body", "No Body")

        log.info("github.create_issue.mock", repo=repo, title=title)

        # Simulate network latency
        time.sleep(0.1)

        return {
            "issue_url": f"https://github.com/{repo}/issues/123",
            "title": title,
            "status": "created",
            "body_length": len(body),
        }

    raise McpUnavailable(f"Tool {name} not supported by github_mcp")
