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
"""OpenMetadata MCP client — thin wrapper around ``data-ai-sdk`` with defense.

Per .idea/Plan/Project/NFRs.md "The 5 Things AI Never Adds":
  - timeout: ``settings.om_timeout_seconds`` (default 5.0 s)
  - retry: 3 attempts, exponential backoff with jitter (tenacity)
  - circuit breaker: open after 5 consecutive failures, 30 s cooldown
  - structured error: maps SDK errors to McpUnavailable / McpAuthFailed

Implements P1-03: search_metadata round-trip, call_tool, list_tools.

SDK layout (data-ai-sdk 0.1.2):
  - ``ai_sdk.AISdk``             — top-level client
  - ``ai_sdk.AISdk.mcp``         — MCPClient property
  - ``ai_sdk.mcp.models.MCPTool``— 11-member StrEnum (excludes create_metric)
  - ``ai_sdk.mcp._client.MCPError / MCPToolExecutionError`` — exceptions

Before first ``AISdk`` construction, ``MCPClient._make_jsonrpc_request`` is patched
once so POST uses ``Settings.om_mcp_http_path`` (``OM_MCP_HTTP_PATH``), because
the SDK hardcodes ``/mcp`` which some OM builds reject with HTTP 405.
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any, cast

import pybreaker
from ai_sdk.mcp._client import MCPError  # type: ignore[attr-defined, unused-ignore]
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from copilot.config import get_settings
from copilot.middleware.error_envelope import McpAuthFailed, McpUnavailable
from copilot.models.mcp_tools import (
    CreateGlossaryParams,
    CreateGlossaryResponse,
    CreateGlossaryTermParams,
    CreateGlossaryTermResponse,
    GetEntityDetailsParams,
    GetEntityDetailsResponse,
    GetEntityLineageParams,
    GetEntityLineageResponse,
    PatchEntityParams,
    PatchEntityResponse,
    SearchMetadataParams,
    SearchMetadataResponse,
)
from copilot.observability import get_logger
from copilot.observability.metrics import agent_mcp_calls_total

__all__ = [
    "MCPError",
    "call_tool",
    "create_glossary_term_typed",
    "create_glossary_typed",
    "get_entity_details_typed",
    "get_entity_lineage_typed",
    "list_tools",
    "patch_entity_typed",
    "search_metadata",
    "search_metadata_typed",
]

log = get_logger(__name__)

# data-ai-sdk hardcodes POST "/mcp" in MCPClient._make_jsonrpc_request. Some OM builds
# return 405 there; OM_MCP_HTTP_PATH (see Settings.om_mcp_http_path) overrides the path.
_mcp_jsonrpc_original: Callable[..., Any] | None = None
_mcp_jsonrpc_patched: bool = False


def _reset_mcp_jsonrpc_path_patch_for_tests() -> None:
    """Undo MCP JSON-RPC path patch (pytest only — restores data-ai-sdk original)."""
    global _mcp_jsonrpc_original, _mcp_jsonrpc_patched
    if _mcp_jsonrpc_original is not None:
        from ai_sdk.mcp import _client as mcp_client_mod  # type: ignore[unused-ignore]

        mcp_client_mod.MCPClient._make_jsonrpc_request = _mcp_jsonrpc_original  # type: ignore[method-assign]
    _mcp_jsonrpc_original = None
    _mcp_jsonrpc_patched = False
    _get_sdk_client.cache_clear()


def _ensure_mcp_jsonrpc_uses_configured_path() -> None:
    """Monkey-patch MCPClient once so JSON-RPC POST uses Settings.om_mcp_http_path."""
    global _mcp_jsonrpc_original, _mcp_jsonrpc_patched
    if _mcp_jsonrpc_patched:
        return

    import uuid

    import httpx
    from ai_sdk.exceptions import AISdkError, MCPError  # type: ignore[unused-ignore]
    from ai_sdk.mcp import _client as mcp_client_mod  # type: ignore[unused-ignore]

    _mcp_jsonrpc_original = mcp_client_mod.MCPClient._make_jsonrpc_request

    def _patched_make_jsonrpc_request(
        self: Any, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        path = get_settings().om_mcp_http_path
        request_id = str(uuid.uuid4())[:8]
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        try:
            result = self._http.post(path, json=payload)
        except (AISdkError, httpx.HTTPError) as exc:
            raise MCPError(f"MCP request failed: {exc}") from exc

        if "error" in result:
            raise MCPError(f"MCP error: {result['error'].get('message', 'Unknown error')}")

        return cast(dict[str, Any], result.get("result", {}))

    mcp_client_mod.MCPClient._make_jsonrpc_request = _patched_make_jsonrpc_request  # type: ignore[method-assign]
    _mcp_jsonrpc_patched = True


# Circuit breaker per NFRs.md: open after 5 consecutive failures, 30 s cooldown.
om_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="om_mcp",
)


# ---------------------------------------------------------------------------
# SDK client singleton
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_sdk_client() -> Any:
    """Lazily initialise the ``AISdk`` client from settings.

    Returns:
        An ``ai_sdk.AISdk`` instance connected to the configured OM host.

    Raises:
        McpUnavailable: If the SDK cannot be initialised (missing dep, bad config).
    """
    settings = get_settings()
    token = settings.ai_sdk_token.get_secret_value()
    if not token:
        raise McpUnavailable("AI_SDK_TOKEN is not set — cannot connect to OM MCP server")

    try:
        from ai_sdk import AISdk  # type: ignore[unused-ignore]
    except ImportError as exc:  # pragma: no cover
        raise McpUnavailable("data-ai-sdk is not installed") from exc

    _ensure_mcp_jsonrpc_uses_configured_path()

    log.info(
        "om.sdk_init",
        host=settings.ai_sdk_host,
        timeout=settings.om_timeout_seconds,
        max_retries=settings.om_max_retries,
        om_mcp_http_path=settings.om_mcp_http_path,
    )
    return AISdk(
        host=settings.ai_sdk_host,
        token=token,
        timeout=settings.om_timeout_seconds,
        max_retries=settings.om_max_retries,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_RETRY_DECORATOR = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=4),
    retry=retry_if_exception_type(McpUnavailable),
    reraise=True,
)


@_RETRY_DECORATOR
def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call an MCP tool by name with circuit-breaker + retry protection.

    Args:
        name: Tool name (must match ``MCPTool`` enum value or ``create_metric``).
        arguments: Tool arguments as a flat dict.

    Returns:
        Parsed JSON dict from the OM MCP server response.

    Raises:
        McpUnavailable: On connection / timeout / server errors or circuit open.
        McpAuthFailed: On 401 / 403 authentication errors.
    """
    log.info("om.call_tool.start", tool=name)
    start = time.monotonic()

    try:
        result = _call_tool_inner(name, arguments)
    except (McpUnavailable, McpAuthFailed):
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.warning("om.call_tool.failed", tool=name, elapsed_ms=elapsed_ms)
        agent_mcp_calls_total.labels(tool_name=name, outcome="fail").inc()
        raise

    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info("om.call_tool.complete", tool=name, elapsed_ms=elapsed_ms)
    agent_mcp_calls_total.labels(tool_name=name, outcome="ok").inc()
    return cast(dict[str, Any], result)


@om_breaker
def _call_tool_inner(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Inner call wrapped by the circuit breaker (separate from retry).

    Raises:
        McpUnavailable: On SDK connection / execution errors.
        McpAuthFailed: On authentication errors (401/403 in error message).
    """
    from ai_sdk.mcp._client import (  # type: ignore[attr-defined, unused-ignore]
        MCPError,
        MCPToolExecutionError,
    )
    from ai_sdk.mcp.models import MCPTool  # type: ignore[unused-ignore]

    sdk = _get_sdk_client()

    # Resolve name → MCPTool enum member if possible; fall back to raw string
    # for tools not in the SDK enum (e.g., create_metric).
    tool_enum: MCPTool | None = None
    with contextlib.suppress(ValueError):
        tool_enum = MCPTool(name)

    try:
        # TODO(tech-debt): _make_jsonrpc_request is private SDK API and could break in patch updates
        if tool_enum is not None:
            result = sdk.mcp.call_tool(tool_enum, arguments)
        else:
            if not hasattr(sdk.mcp, "_make_jsonrpc_request"):
                raise RuntimeError("data-ai-sdk removed internal _make_jsonrpc_request")
            # Direct JSON-RPC for tools not in the SDK enum (create_metric).
            result_raw = sdk.mcp._make_jsonrpc_request(
                "tools/call",
                {"name": name, "arguments": arguments},
            )
            from ai_sdk.mcp.models import ToolCallResult  # type: ignore[unused-ignore]

            is_error = result_raw.get("isError", False)
            content = result_raw.get("content", [])
            text = ""
            if content:
                first = content[0]
                if first.get("type") == "text":
                    text = first.get("text", "")
            if is_error:
                raise MCPToolExecutionError(tool=name, message=text or "Tool execution failed")

            import json

            data: dict[str, Any] = {}
            if text:
                try:
                    data = json.loads(text)
                except (json.JSONDecodeError, ValueError):
                    data = {"text": text}
            result = ToolCallResult(success=True, data=data, error=None)

    except MCPToolExecutionError as exc:
        raise McpUnavailable(f"Tool {name} execution failed: {exc}") from exc
    except MCPError as exc:
        err_msg = str(exc).lower()
        if "401" in err_msg or "403" in err_msg or "unauthorized" in err_msg:
            raise McpAuthFailed(f"OM auth failed for tool {name}") from exc
        raise McpUnavailable(f"MCP error calling {name}: {exc}") from exc
    except pybreaker.CircuitBreakerError as exc:
        raise McpUnavailable("OM MCP circuit breaker is open — too many recent failures") from exc
    except Exception as exc:
        raise McpUnavailable(f"Unexpected error calling {name}: {type(exc).__name__}") from exc

    if not result.success:
        raise McpUnavailable(result.error or f"Tool {name} returned unsuccessful result")

    return result.data or {}


def list_tools() -> list[str]:
    """Return the list of tool names the OM MCP server exposes.

    Returns:
        List of tool name strings.

    Raises:
        McpUnavailable: If the MCP server is unreachable.
    """
    log.info("om.list_tools.start")
    try:
        sdk = _get_sdk_client()
        tools = sdk.mcp.list_tools()
        names = [t.name for t in tools]
        log.info("om.list_tools.complete", count=len(names))
        return names
    except Exception as exc:
        log.error("om.list_tools.failed", error=str(exc))
        raise McpUnavailable(f"Failed to list MCP tools: {exc}") from exc


def search_metadata(
    query: str,
    *,
    entity_type: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Convenience wrapper for the ``search_metadata`` MCP tool.

    Args:
        query: Natural-language or keyword search query.
        entity_type: Optional entity type filter (e.g., "table", "topic").
        limit: Maximum number of results to return.

    Returns:
        Parsed JSON dict with search results from OM.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    arguments: dict[str, Any] = {"query": query}
    if entity_type is not None:
        arguments["entityType"] = entity_type
    if limit != 10:
        arguments["limit"] = limit

    return call_tool("search_metadata", arguments)


# ---------------------------------------------------------------------------
# Typed wrappers (P1-09: issue #22)
# ---------------------------------------------------------------------------


def search_metadata_typed(params: SearchMetadataParams) -> SearchMetadataResponse:
    """Search metadata with typed input validation and response parsing.

    Args:
        params: Validated search parameters.

    Returns:
        Parsed ``SearchMetadataResponse`` with typed hits.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    raw = call_tool(
        "search_metadata",
        params.model_dump(by_alias=True, exclude_none=True),
    )

    # The OM server returns search hits under various shapes.  Normalise to
    # the ``hits`` / ``total`` structure our response model expects.
    hits_raw = raw.get("hits", raw.get("data", []))
    if isinstance(hits_raw, dict):
        hits_raw = hits_raw.get("hits", [])
    total = raw.get("total", raw.get("totalCount", len(hits_raw)))

    return SearchMetadataResponse.model_validate(
        {**raw, "hits": hits_raw, "total": total},
    )


def get_entity_details_typed(
    params: GetEntityDetailsParams,
) -> GetEntityDetailsResponse:
    """Get entity details with typed input validation and response parsing.

    Args:
        params: Validated entity lookup parameters.

    Returns:
        Parsed ``GetEntityDetailsResponse`` with entity fields.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    raw = call_tool(
        "get_entity_details",
        params.model_dump(by_alias=True, exclude_none=True),
    )
    return GetEntityDetailsResponse.model_validate(raw)


def get_entity_lineage_typed(
    params: GetEntityLineageParams,
) -> GetEntityLineageResponse:
    """Get entity lineage with typed input validation and response parsing.

    Args:
        params: Validated lineage query parameters.

    Returns:
        Parsed ``GetEntityLineageResponse`` with nodes and edges.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    raw = call_tool(
        "get_entity_lineage",
        params.model_dump(by_alias=True, exclude_none=True),
    )
    return GetEntityLineageResponse.model_validate(raw)


def create_glossary_typed(params: CreateGlossaryParams) -> CreateGlossaryResponse:
    """Create a glossary with typed input validation and response parsing.

    Args:
        params: Validated glossary creation parameters.

    Returns:
        Parsed ``CreateGlossaryResponse`` with the created entity.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    raw = call_tool(
        "create_glossary",
        params.model_dump(by_alias=True, exclude_none=True),
    )
    return CreateGlossaryResponse.model_validate(raw)


def create_glossary_term_typed(
    params: CreateGlossaryTermParams,
) -> CreateGlossaryTermResponse:
    """Create a glossary term with typed input validation and response parsing.

    Args:
        params: Validated glossary term creation parameters.

    Returns:
        Parsed ``CreateGlossaryTermResponse`` with the created entity.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    raw = call_tool(
        "create_glossary_term",
        params.model_dump(by_alias=True, exclude_none=True),
    )
    return CreateGlossaryTermResponse.model_validate(raw)


def patch_entity_typed(params: PatchEntityParams) -> PatchEntityResponse:
    """Patch an entity with typed input validation and response parsing.

    Args:
        params: Validated entity patch parameters.

    Returns:
        Parsed ``PatchEntityResponse`` with the updated entity.

    Raises:
        McpUnavailable: On connection / timeout errors.
        McpAuthFailed: On authentication errors.
    """
    raw = call_tool(
        "patch_entity",
        params.model_dump(by_alias=True, exclude_none=True),
    )
    return PatchEntityResponse.model_validate(raw)
