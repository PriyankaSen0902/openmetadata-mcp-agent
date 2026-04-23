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
"""Integration tests for GET /api/v1/governance/drift with mocked MCP.

Tests cover:
  - 200 with empty drift list (first scan, no baseline)
  - 200 with drift items (hash change detected on second scan)
  - 503 when OM is unreachable (circuit breaker / MCP error)
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set safe defaults BEFORE any app import
os.environ.setdefault("AI_SDK_TOKEN", "test-token-placeholder-not-real-jwt")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder-not-real-key")
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "warning")

from copilot.middleware.error_envelope import McpUnavailable
from copilot.services.drift import reset_state, run_drift_scan


@pytest.fixture(autouse=True)
def _clean_drift_state() -> Iterator[None]:
    """Reset drift module state before each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """FastAPI test client with drift poll disabled (no background tasks)."""

    async def _dummy(*args, **kwargs):
        pass

    with patch("copilot.api.main._drift_poll_loop", side_effect=_dummy):
        from copilot.api.main import create_app

        app = create_app()
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# GET /api/v1/governance/drift
# ---------------------------------------------------------------------------


class TestDriftEndpoint:
    """Integration tests for the governance/drift route."""

    def test_drift_200_empty_before_scan(self, client: TestClient) -> None:
        """Before any scan, drift list should be empty (no error)."""
        resp = client.get("/api/v1/governance/drift")
        assert resp.status_code == 200
        body = resp.json()
        assert body["drift"] == []
        assert body["drift_count"] == 0

    def test_drift_200_after_clean_scan(self, client: TestClient) -> None:
        """After a first scan with mocked MCP, drift is empty (baseline set)."""
        mock_search = {
            "hits": [
                {"fullyQualifiedName": "db.schema.table1", "entityType": "table"},
            ],
        }
        mock_entity = {
            "description": "A table",
            "columns": [{"name": "id", "dataType": "INT", "tags": []}],
            "tags": [{"tagFQN": "Tier.Tier1"}],
        }

        def mock_call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
            if name == "search_metadata":
                return mock_search
            return mock_entity

        with patch("copilot.services.drift.om_mcp.call_tool", side_effect=mock_call_tool):
            asyncio.run(run_drift_scan())

        resp = client.get("/api/v1/governance/drift")
        assert resp.status_code == 200
        body = resp.json()
        assert body["drift_count"] == 0
        assert body["entity_count"] == 1

    def test_drift_200_detects_hash_change(self, client: TestClient) -> None:
        """After baseline set, changing an entity should produce drift items."""
        mock_search = {
            "hits": [
                {"fullyQualifiedName": "db.schema.table1", "entityType": "table"},
            ],
        }
        original_entity = {
            "description": "Original",
            "columns": [],
            "tags": [{"tagFQN": "PII.Sensitive"}],
        }
        modified_entity = {
            "description": "Modified by someone",
            "columns": [],
            "tags": [],  # PII tag removed
        }

        # First scan: establish baseline
        def mock_call_tool_v1(name: str, args: dict[str, Any]) -> dict[str, Any]:
            if name == "search_metadata":
                return mock_search
            return original_entity

        with patch("copilot.services.drift.om_mcp.call_tool", side_effect=mock_call_tool_v1):
            asyncio.run(run_drift_scan())

        # Second scan: entity changed
        def mock_call_tool_v2(name: str, args: dict[str, Any]) -> dict[str, Any]:
            if name == "search_metadata":
                return mock_search
            return modified_entity

        with patch("copilot.services.drift.om_mcp.call_tool", side_effect=mock_call_tool_v2):
            asyncio.run(run_drift_scan())

        resp = client.get("/api/v1/governance/drift")
        assert resp.status_code == 200
        body = resp.json()
        assert body["drift_count"] >= 1
        signals = [d["signal"] for d in body["drift"]]
        assert "hash_changed" in signals
        # PII tag was removed — should also appear
        assert "tag_missing" in signals

    def test_drift_503_when_om_down(self, client: TestClient) -> None:
        """When OM is unreachable, GET drift returns 503 per contract."""
        with patch(
            "copilot.services.drift.om_mcp.call_tool",
            side_effect=McpUnavailable("connection refused"),
        ):
            asyncio.run(run_drift_scan())

        resp = client.get("/api/v1/governance/drift")
        assert resp.status_code == 503
        body = resp.json()
        assert body["code"] == "om_unavailable"
