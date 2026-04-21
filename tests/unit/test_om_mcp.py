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
"""Unit tests for copilot.clients.om_mcp — MCP client wrapper.

Tests mock the ai_sdk layer and verify:
- Happy path returns parsed data
- SDK errors map to McpUnavailable / McpAuthFailed
- Circuit breaker opens after repeated failures
- search_metadata convenience wrapper works
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pybreaker
import pytest

from copilot.clients import om_mcp
from copilot.middleware.error_envelope import McpAuthFailed, McpUnavailable


@dataclass
class _FakeToolCallResult:
    success: bool
    data: dict[str, Any] | None
    error: str | None


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset module-level caches and circuit breaker between tests."""
    om_mcp._get_sdk_client.cache_clear()
    om_mcp.om_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="om_mcp_test")
    yield
    om_mcp._get_sdk_client.cache_clear()


def _mock_sdk(
    tool_result: _FakeToolCallResult | None = None, side_effect: Exception | None = None
) -> MagicMock:
    """Create a mock AISdk instance with a configured mcp.call_tool."""
    sdk = MagicMock()
    if side_effect:
        sdk.mcp.call_tool.side_effect = side_effect
    elif tool_result:
        sdk.mcp.call_tool.return_value = tool_result
    return sdk


class TestCallTool:
    """Tests for om_mcp.call_tool()."""

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_returns_data_on_success(self, mock_get_sdk: MagicMock) -> None:
        """Happy path: SDK returns a successful ToolCallResult with data."""
        result_data = {"tables": [{"fqn": "db.schema.users"}]}
        mock_get_sdk.return_value = _mock_sdk(
            tool_result=_FakeToolCallResult(success=True, data=result_data, error=None)
        )

        result = om_mcp.call_tool("search_metadata", {"query": "users"})

        assert result == result_data
        mock_get_sdk.return_value.mcp.call_tool.assert_called_once()

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_unavailable_on_sdk_error(self, mock_get_sdk: MagicMock) -> None:
        from copilot.clients.om_mcp import MCPError

        mock_get_sdk.return_value = _mock_sdk(side_effect=MCPError("connection refused"))

        with pytest.raises(McpUnavailable):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_auth_failed_on_401(self, mock_get_sdk: MagicMock) -> None:
        from copilot.clients.om_mcp import MCPError

        mock_get_sdk.return_value = _mock_sdk(side_effect=MCPError("MCP error: 401 Unauthorized"))

        with pytest.raises(McpAuthFailed):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_unavailable_on_unsuccessful_result(self, mock_get_sdk: MagicMock) -> None:
        """ToolCallResult with success=False raises McpUnavailable."""
        mock_get_sdk.return_value = _mock_sdk(
            tool_result=_FakeToolCallResult(success=False, data=None, error="something went wrong")
        )

        with pytest.raises((McpUnavailable, pybreaker.CircuitBreakerError)):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_circuit_breaker_opens_after_5_failures(self, mock_get_sdk: MagicMock) -> None:
        from copilot.clients.om_mcp import MCPError

        # Fresh breaker for this test to avoid pollution
        om_mcp.om_breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=300, name="om_mcp_breaker_test"
        )

        mock_get_sdk.return_value = _mock_sdk(side_effect=MCPError("timeout"))

        # Burn through 5 failures to trigger breaker open
        for _ in range(5):
            with pytest.raises((McpUnavailable, pybreaker.CircuitBreakerError)):
                om_mcp._call_tool_inner("search_metadata", {"query": "test"})

        # 6th call should get circuit breaker error (open state)
        with pytest.raises(pybreaker.CircuitBreakerError):
            om_mcp._call_tool_inner("search_metadata", {"query": "test"})


class TestSearchMetadata:
    """Tests for om_mcp.search_metadata() convenience wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_passes_query_to_call_tool(self, mock_call_tool: MagicMock) -> None:
        """search_metadata delegates to call_tool with correct arguments."""
        mock_call_tool.return_value = {"hits": []}

        result = om_mcp.search_metadata("customer tables", entity_type="table")

        mock_call_tool.assert_called_once_with(
            "search_metadata",
            {"query": "customer tables", "entity_type": "table"},
        )
        assert result == {"hits": []}

    @patch("copilot.clients.om_mcp.call_tool")
    def test_omits_optional_params_when_default(self, mock_call_tool: MagicMock) -> None:
        """search_metadata omits entity_type and limit when using defaults."""
        mock_call_tool.return_value = {}

        om_mcp.search_metadata("schema")

        mock_call_tool.assert_called_once_with(
            "search_metadata",
            {"query": "schema"},
        )


class TestListTools:
    """Tests for om_mcp.list_tools()."""

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_returns_tool_names(self, mock_get_sdk: MagicMock) -> None:
        """list_tools returns a list of tool name strings."""
        mock_tool_1 = MagicMock()
        mock_tool_1.name = "search_metadata"
        mock_tool_2 = MagicMock()
        mock_tool_2.name = "get_entity_details"

        sdk = MagicMock()
        sdk.mcp.list_tools.return_value = [mock_tool_1, mock_tool_2]
        mock_get_sdk.return_value = sdk

        names = om_mcp.list_tools()

        assert names == ["search_metadata", "get_entity_details"]
