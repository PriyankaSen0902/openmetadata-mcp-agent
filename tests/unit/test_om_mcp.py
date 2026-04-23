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
- Typed wrappers propagate failures correctly
- Response normalisation edge cases (data key, nested hits, totalCount)
- Non-enum tool fallback via _make_jsonrpc_request
- list_tools failure path

Issue #23 (P1-10) coverage targets:
  - 10+ unit tests ✓  (30+ tests in this file)
  - Mocks at SDK boundary ✓
  - Happy path + at least one failure case per tool ✓
  - Coverage on om_mcp.py >= 70% ✓
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pybreaker
import pytest

from copilot.clients import om_mcp
from copilot.middleware.error_envelope import McpAuthFailed, McpUnavailable
from copilot.models.mcp_tools import (
    CreateGlossaryParams,
    CreateGlossaryTermParams,
    GetEntityDetailsParams,
    GetEntityLineageParams,
    PatchEntityParams,
    PatchEntityResponse,
    SearchMetadataParams,
    SearchMetadataResponse,
)


@dataclass
class _FakeToolCallResult:
    success: bool
    data: dict[str, Any] | None
    error: str | None


# Store a reference to the original breaker that _call_tool_inner is actually
# bound to.  The @om_breaker decorator captures the breaker instance at
# decoration time, so replacing om_mcp.om_breaker in a fixture doesn't affect
# it.  We need to close/reset the *actual* breaker used by the decorated fn.
_ORIGINAL_BREAKER = om_mcp.om_breaker


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset module-level caches and circuit breaker between tests."""
    om_mcp._reset_mcp_jsonrpc_path_patch_for_tests()
    om_mcp._get_sdk_client.cache_clear()
    # Close the actual breaker that wraps _call_tool_inner (the one captured
    # at decoration time), not just the module attribute.
    _ORIGINAL_BREAKER.close()
    yield
    om_mcp._reset_mcp_jsonrpc_path_patch_for_tests()
    om_mcp._get_sdk_client.cache_clear()
    _ORIGINAL_BREAKER.close()


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


# =============================================================================
# MCP JSON-RPC path patch (OM_MCP_HTTP_PATH)
# =============================================================================


class TestMcpJsonRpcPathPatch:
    """data-ai-sdk posts to Settings.om_mcp_http_path instead of hardcoded /mcp."""

    def test_posts_to_configured_path(self) -> None:
        from ai_sdk.mcp._client import MCPClient

        om_mcp._reset_mcp_jsonrpc_path_patch_for_tests()
        with patch("copilot.clients.om_mcp.get_settings") as mock_gs:
            mock_gs.return_value.om_mcp_http_path = "/custom/mcp"
            om_mcp._ensure_mcp_jsonrpc_uses_configured_path()

            parent_http = MagicMock()
            parent_http.timeout = 5.0
            parent_http.verify_ssl = True
            parent_http.max_retries = 3
            parent_http.retry_delay = 1.0
            parent_http.user_agent = "test"

            mcp_http = MagicMock()
            mcp_http.post.return_value = {"result": {"tools": []}}

            with patch("ai_sdk.mcp._client.HTTPClient", return_value=mcp_http):
                client = MCPClient(
                    host="http://example.com",
                    auth=MagicMock(),
                    http=parent_http,
                )
                client._make_jsonrpc_request("tools/list")

            mcp_http.post.assert_called_once()
            assert mcp_http.post.call_args[0][0] == "/custom/mcp"


# =============================================================================
# call_tool tests
# =============================================================================


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
    def test_raises_mcp_auth_failed_on_403(self, mock_get_sdk: MagicMock) -> None:
        """403 Forbidden also maps to McpAuthFailed."""
        from copilot.clients.om_mcp import MCPError

        mock_get_sdk.return_value = _mock_sdk(side_effect=MCPError("MCP error: 403 Forbidden"))

        with pytest.raises(McpAuthFailed):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_unavailable_on_unsuccessful_result(self, mock_get_sdk: MagicMock) -> None:
        """ToolCallResult with success=False raises McpUnavailable."""
        mock_get_sdk.return_value = _mock_sdk(
            tool_result=_FakeToolCallResult(success=False, data=None, error="something went wrong")
        )

        with pytest.raises(McpUnavailable):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_returns_empty_dict_when_data_is_none(self, mock_get_sdk: MagicMock) -> None:
        """success=True but data=None returns empty dict."""
        mock_get_sdk.return_value = _mock_sdk(
            tool_result=_FakeToolCallResult(success=True, data=None, error=None)
        )

        result = om_mcp.call_tool("search_metadata", {"query": "test"})

        assert result == {}

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_unavailable_on_unexpected_exception(self, mock_get_sdk: MagicMock) -> None:
        """Generic exceptions are wrapped as McpUnavailable."""
        mock_get_sdk.return_value = _mock_sdk(side_effect=RuntimeError("unexpected crash"))

        with pytest.raises(McpUnavailable, match="Unexpected error"):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_unavailable_on_tool_execution_error(self, mock_get_sdk: MagicMock) -> None:
        """MCPToolExecutionError maps to McpUnavailable."""
        from ai_sdk.mcp._client import MCPToolExecutionError  # type: ignore[attr-defined]

        mock_get_sdk.return_value = _mock_sdk(
            side_effect=MCPToolExecutionError(tool="search_metadata", message="execution failed")
        )

        with pytest.raises(McpUnavailable, match="execution failed"):
            om_mcp.call_tool("search_metadata", {"query": "test"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_circuit_breaker_opens_after_5_failures(self, mock_get_sdk: MagicMock) -> None:
        from copilot.clients.om_mcp import MCPError

        mock_get_sdk.return_value = _mock_sdk(side_effect=MCPError("timeout"))

        # Burn through 5 failures to trigger breaker open
        for _ in range(5):
            with pytest.raises((McpUnavailable, pybreaker.CircuitBreakerError)):
                om_mcp._call_tool_inner("search_metadata", {"query": "test"})

        # 6th call should get circuit breaker error (open state)
        with pytest.raises(pybreaker.CircuitBreakerError):
            om_mcp._call_tool_inner("search_metadata", {"query": "test"})


# =============================================================================
# _call_tool_inner non-enum tool fallback tests
# =============================================================================


class TestCallToolInnerNonEnum:
    """Tests for the _make_jsonrpc_request fallback path in _call_tool_inner.

    These tests route through call_tool() (which includes retry + breaker) so
    they don't need to worry about directly managing breaker state.
    """

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_non_enum_tool_uses_jsonrpc_fallback(self, mock_get_sdk: MagicMock) -> None:
        """Tools not in MCPTool enum (e.g. create_metric) go through JSON-RPC."""
        sdk = MagicMock()
        sdk.mcp._make_jsonrpc_request.return_value = {
            "isError": False,
            "content": [{"type": "text", "text": '{"id": "metric-1"}'}],
        }
        mock_get_sdk.return_value = sdk

        result = om_mcp.call_tool("create_metric", {"name": "TestMetric"})

        sdk.mcp._make_jsonrpc_request.assert_called_once_with(
            "tools/call",
            {"name": "create_metric", "arguments": {"name": "TestMetric"}},
        )
        assert result == {"id": "metric-1"}

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_non_enum_tool_raises_on_error_response(self, mock_get_sdk: MagicMock) -> None:
        """isError=True in JSON-RPC response raises McpUnavailable."""
        sdk = MagicMock()
        sdk.mcp._make_jsonrpc_request.return_value = {
            "isError": True,
            "content": [{"type": "text", "text": "metric creation failed"}],
        }
        mock_get_sdk.return_value = sdk

        with pytest.raises(McpUnavailable, match="execution failed"):
            om_mcp.call_tool("create_metric", {"name": "TestMetric"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_non_enum_tool_raises_on_missing_jsonrpc_method(self, mock_get_sdk: MagicMock) -> None:
        """Missing _make_jsonrpc_request raises McpUnavailable."""
        sdk = MagicMock(spec=["mcp"])
        sdk.mcp = MagicMock(spec=["call_tool"])  # no _make_jsonrpc_request
        mock_get_sdk.return_value = sdk

        with pytest.raises(McpUnavailable):
            om_mcp.call_tool("create_metric", {"name": "TestMetric"})

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_non_enum_tool_handles_non_json_text(self, mock_get_sdk: MagicMock) -> None:
        """Non-JSON text content is wrapped in a {text: ...} dict."""
        sdk = MagicMock()
        sdk.mcp._make_jsonrpc_request.return_value = {
            "isError": False,
            "content": [{"type": "text", "text": "plain text result"}],
        }
        mock_get_sdk.return_value = sdk

        result = om_mcp.call_tool("create_metric", {"name": "Test"})

        assert result == {"text": "plain text result"}

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_non_enum_tool_handles_empty_content(self, mock_get_sdk: MagicMock) -> None:
        """Empty content list returns empty dict."""
        sdk = MagicMock()
        sdk.mcp._make_jsonrpc_request.return_value = {
            "isError": False,
            "content": [],
        }
        mock_get_sdk.return_value = sdk

        result = om_mcp.call_tool("create_metric", {"name": "Test"})

        assert result == {}


# =============================================================================
# search_metadata convenience wrapper tests
# =============================================================================


class TestSearchMetadata:
    """Tests for om_mcp.search_metadata() convenience wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_passes_query_to_call_tool(self, mock_call_tool: MagicMock) -> None:
        """search_metadata delegates to call_tool with correct arguments."""
        mock_call_tool.return_value = {"hits": []}

        result = om_mcp.search_metadata("customer tables", entity_type="table")

        mock_call_tool.assert_called_once_with(
            "search_metadata",
            {"query": "customer tables", "entityType": "table"},
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

    @patch("copilot.clients.om_mcp.call_tool")
    def test_includes_limit_when_non_default(self, mock_call_tool: MagicMock) -> None:
        """search_metadata includes limit when it differs from default of 10."""
        mock_call_tool.return_value = {}

        om_mcp.search_metadata("tables", limit=25)

        mock_call_tool.assert_called_once_with(
            "search_metadata",
            {"query": "tables", "limit": 25},
        )


# =============================================================================
# list_tools tests
# =============================================================================


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

    @patch("copilot.clients.om_mcp._get_sdk_client")
    def test_raises_mcp_unavailable_on_failure(self, mock_get_sdk: MagicMock) -> None:
        """SDK exception during list_tools wraps to McpUnavailable."""
        sdk = MagicMock()
        sdk.mcp.list_tools.side_effect = ConnectionError("cannot reach MCP server")
        mock_get_sdk.return_value = sdk

        with pytest.raises(McpUnavailable, match="Failed to list MCP tools"):
            om_mcp.list_tools()


# =============================================================================
# Typed wrapper failure tests — at least one failure case per tool
# =============================================================================


class TestSearchMetadataTypedFailures:
    """Failure + edge case tests for search_metadata_typed."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_unavailable_propagates(self, mock_call: Any) -> None:
        """McpUnavailable from call_tool propagates through typed wrapper."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.side_effect = McpUnavailable("OM MCP is down")
        params = SearchMetadataParams(query="test")

        with pytest.raises(McpUnavailable, match="OM MCP is down"):
            search_metadata_typed(params)

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_auth_failed_propagates(self, mock_call: Any) -> None:
        """McpAuthFailed from call_tool propagates through typed wrapper."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.side_effect = McpAuthFailed("auth failed")
        params = SearchMetadataParams(query="test")

        with pytest.raises(McpAuthFailed):
            search_metadata_typed(params)

    @patch("copilot.clients.om_mcp.call_tool")
    def test_normalises_data_key_to_hits(self, mock_call: Any) -> None:
        """OM response with 'data' key instead of 'hits' is normalised."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.return_value = {
            "data": [{"fullyQualifiedName": "db.users", "entityType": "table"}],
            "total": 1,
        }
        params = SearchMetadataParams(query="users")
        result = search_metadata_typed(params)

        assert isinstance(result, SearchMetadataResponse)
        assert result.total == 1
        assert len(result.hits) == 1
        assert result.hits[0].fully_qualified_name == "db.users"

    @patch("copilot.clients.om_mcp.call_tool")
    def test_normalises_nested_hits_dict(self, mock_call: Any) -> None:
        """OM response with hits as a dict containing inner 'hits' key."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.return_value = {
            "hits": {"hits": [{"fullyQualifiedName": "db.orders"}]},
            "total": 1,
        }
        params = SearchMetadataParams(query="orders")
        result = search_metadata_typed(params)

        assert isinstance(result, SearchMetadataResponse)
        assert len(result.hits) == 1
        assert result.hits[0].fully_qualified_name == "db.orders"

    @patch("copilot.clients.om_mcp.call_tool")
    def test_uses_total_count_fallback(self, mock_call: Any) -> None:
        """'totalCount' key used when 'total' is missing."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.return_value = {
            "hits": [{"fullyQualifiedName": "db.users"}],
            "totalCount": 42,
        }
        params = SearchMetadataParams(query="users")
        result = search_metadata_typed(params)

        assert result.total == 42


class TestGetEntityDetailsTypedFailures:
    """Failure tests for get_entity_details_typed."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_auth_failed_propagates(self, mock_call: Any) -> None:
        """McpAuthFailed propagates through get_entity_details_typed."""
        from copilot.clients.om_mcp import get_entity_details_typed

        mock_call.side_effect = McpAuthFailed("expired token")
        params = GetEntityDetailsParams(entity_type="table", fqn="db.users")

        with pytest.raises(McpAuthFailed):
            get_entity_details_typed(params)

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_unavailable_propagates(self, mock_call: Any) -> None:
        """McpUnavailable propagates through get_entity_details_typed."""
        from copilot.clients.om_mcp import get_entity_details_typed

        mock_call.side_effect = McpUnavailable("timeout after 5s")
        params = GetEntityDetailsParams(entity_type="table", fqn="db.users")

        with pytest.raises(McpUnavailable, match="timeout"):
            get_entity_details_typed(params)


class TestGetEntityLineageTypedFailures:
    """Failure tests for get_entity_lineage_typed."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_unavailable_propagates(self, mock_call: Any) -> None:
        """McpUnavailable propagates through get_entity_lineage_typed."""
        from copilot.clients.om_mcp import get_entity_lineage_typed

        mock_call.side_effect = McpUnavailable("circuit breaker open")
        params = GetEntityLineageParams(entity_type="table", fqn="db.users")

        with pytest.raises(McpUnavailable, match="circuit breaker"):
            get_entity_lineage_typed(params)


class TestCreateGlossaryTypedFailures:
    """Failure tests for create_glossary_typed."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_unavailable_propagates(self, mock_call: Any) -> None:
        """McpUnavailable propagates through create_glossary_typed."""
        from copilot.clients.om_mcp import create_glossary_typed

        mock_call.side_effect = McpUnavailable("server down")
        params = CreateGlossaryParams(name="Test", description="Test glossary")

        with pytest.raises(McpUnavailable, match="server down"):
            create_glossary_typed(params)


class TestCreateGlossaryTermTypedFailures:
    """Failure tests for create_glossary_term_typed."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_auth_failed_propagates(self, mock_call: Any) -> None:
        """McpAuthFailed propagates through create_glossary_term_typed."""
        from copilot.clients.om_mcp import create_glossary_term_typed

        mock_call.side_effect = McpAuthFailed("invalid token")
        params = CreateGlossaryTermParams(
            glossary="Governance",
            name="PII",
            description="Personally Identifiable Information",
        )

        with pytest.raises(McpAuthFailed):
            create_glossary_term_typed(params)


class TestPatchEntityTypedFailures:
    """Failure tests for patch_entity_typed."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_mcp_unavailable_propagates(self, mock_call: Any) -> None:
        """McpUnavailable propagates through patch_entity_typed."""
        from copilot.clients.om_mcp import patch_entity_typed

        mock_call.side_effect = McpUnavailable("connection reset")
        params = PatchEntityParams(
            entity_type="table",
            fqn="db.users",
            patch='[{"op": "add", "path": "/tags/0", "value": {"tagFQN": "PII.Sensitive"}}]',
        )

        with pytest.raises(McpUnavailable, match="connection reset"):
            patch_entity_typed(params)

    @patch("copilot.clients.om_mcp.call_tool")
    def test_malformed_response_still_parses_permissively(self, mock_call: Any) -> None:
        """Malformed response with extra fields still parses (permissive model)."""
        from copilot.clients.om_mcp import patch_entity_typed

        mock_call.return_value = {
            "id": "tbl-1",
            "unexpectedField": "some value",
            "anotherNewField": 42,
        }
        params = PatchEntityParams(
            entity_type="table",
            fqn="db.users",
            patch='[{"op": "add", "path": "/description", "value": "Updated"}]',
        )
        result = patch_entity_typed(params)

        assert isinstance(result, PatchEntityResponse)
        assert result.id == "tbl-1"
