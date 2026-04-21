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
"""Unit tests for copilot.models.mcp_tools and typed wrappers in om_mcp.

Tests cover:
  - Params validation: required fields, type coercion, alias mapping, defaults
  - Response parsing: happy path, extra fields ignored, missing optional fields
  - Typed wrapper functions: mock call_tool, verify Params→dict→Response round-trip
  - Edge cases: empty results, validation errors
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

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

# =============================================================================
# Params validation tests
# =============================================================================


class TestSearchMetadataParams:
    """Tests for SearchMetadataParams validation."""

    def test_defaults_only(self) -> None:
        """All params are optional; defaults produce a valid model."""
        params = SearchMetadataParams()

        assert params.query is None
        assert params.entity_type is None
        assert params.from_ == 0
        assert params.size == 10
        assert params.include_deleted is False

    def test_all_fields(self) -> None:
        """All fields set explicitly."""
        params = SearchMetadataParams(
            query="customer",
            entity_type="table",
            from_=10,
            size=50,
            include_deleted=True,
            fields="columns,queries",
            include_aggregations=True,
            max_aggregation_buckets=20,
        )

        assert params.query == "customer"
        assert params.entity_type == "table"
        assert params.from_ == 10
        assert params.size == 50

    def test_alias_serialization(self) -> None:
        """Serialization uses camelCase aliases for SDK compatibility."""
        params = SearchMetadataParams(
            entity_type="table",
            include_deleted=True,
        )
        dumped = params.model_dump(by_alias=True, exclude_none=True)

        assert "entityType" in dumped
        assert "includeDeleted" in dumped
        assert dumped["entityType"] == "table"
        assert dumped["includeDeleted"] is True

    def test_size_validation_max(self) -> None:
        """Size > 50 is rejected."""
        with pytest.raises(ValidationError, match="less than or equal to 50"):
            SearchMetadataParams(size=51)

    def test_size_validation_min(self) -> None:
        """Size < 1 is rejected."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            SearchMetadataParams(size=0)

    def test_extra_fields_rejected(self) -> None:
        """Extra fields are rejected (strict params)."""
        with pytest.raises(ValidationError, match="extra"):
            SearchMetadataParams(unknown_field="value")  # type: ignore[call-arg]

    def test_none_fields_excluded(self) -> None:
        """None fields are excluded from dump when exclude_none=True."""
        params = SearchMetadataParams(query="test")
        dumped = params.model_dump(by_alias=True, exclude_none=True)

        assert "entityType" not in dumped
        assert "queryFilter" not in dumped
        assert "query" in dumped


class TestGetEntityDetailsParams:
    """Tests for GetEntityDetailsParams validation."""

    def test_required_fields(self) -> None:
        """entityType and fqn are required."""
        params = GetEntityDetailsParams(
            entity_type="table",
            fqn="service.db.schema.table",
        )
        assert params.entity_type == "table"
        assert params.fqn == "service.db.schema.table"

    def test_missing_required_raises(self) -> None:
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            GetEntityDetailsParams()  # type: ignore[call-arg]

    def test_alias_dump(self) -> None:
        """Dump produces camelCase alias."""
        params = GetEntityDetailsParams(entity_type="table", fqn="test.table")
        dumped = params.model_dump(by_alias=True)

        assert dumped["entityType"] == "table"
        assert dumped["fqn"] == "test.table"


class TestGetEntityLineageParams:
    """Tests for GetEntityLineageParams validation."""

    def test_defaults(self) -> None:
        """Depth defaults to 3."""
        params = GetEntityLineageParams(entity_type="table", fqn="a.b.c")

        assert params.upstream_depth == 3
        assert params.downstream_depth == 3

    def test_depth_max_validation(self) -> None:
        """Depth > 10 is rejected."""
        with pytest.raises(ValidationError, match="less than or equal to 10"):
            GetEntityLineageParams(
                entity_type="table",
                fqn="a.b.c",
                upstream_depth=11,
            )


class TestCreateGlossaryParams:
    """Tests for CreateGlossaryParams validation."""

    def test_required_fields(self) -> None:
        """name and description are required."""
        params = CreateGlossaryParams(
            name="Governance",
            description="Core governance glossary",
        )
        assert params.name == "Governance"
        assert params.mutually_exclusive is False

    def test_empty_name_rejected(self) -> None:
        """Empty name is rejected."""
        with pytest.raises(ValidationError, match="at least 1"):
            CreateGlossaryParams(name="", description="test")

    def test_optional_owners(self) -> None:
        """owners is optional."""
        params = CreateGlossaryParams(
            name="Test",
            description="Test glossary",
            owners=["admin", "team_lead"],
        )
        assert params.owners == ["admin", "team_lead"]


class TestCreateGlossaryTermParams:
    """Tests for CreateGlossaryTermParams validation."""

    def test_required_fields(self) -> None:
        """glossary, name, description are required."""
        params = CreateGlossaryTermParams(
            glossary="Governance",
            name="PII",
            description="Personally Identifiable Information",
        )
        assert params.glossary == "Governance"

    def test_parent_term_alias(self) -> None:
        """parentTerm alias works correctly."""
        params = CreateGlossaryTermParams(
            glossary="Governance",
            name="Email",
            description="Email address",
            parent_term="Governance.PII",
        )
        dumped = params.model_dump(by_alias=True, exclude_none=True)

        assert dumped["parentTerm"] == "Governance.PII"


class TestPatchEntityParams:
    """Tests for PatchEntityParams validation."""

    def test_required_fields(self) -> None:
        """entityType, fqn, patch are all required."""
        params = PatchEntityParams(
            entity_type="table",
            fqn="db.schema.users",
            patch='[{"op": "add", "path": "/tags/0", "value": {"tagFQN": "PII.Sensitive"}}]',
        )
        assert params.entity_type == "table"

    def test_patch_min_length(self) -> None:
        """patch must be at least 2 chars (shortest valid: '[]')."""
        with pytest.raises(ValidationError, match="at least 2"):
            PatchEntityParams(entity_type="table", fqn="test", patch="")


# =============================================================================
# Response parsing tests
# =============================================================================


class TestSearchMetadataResponse:
    """Tests for SearchMetadataResponse parsing."""

    def test_parse_happy_path(self) -> None:
        """Parse a response with hits."""
        raw = {
            "hits": [
                {"fullyQualifiedName": "db.users", "entityType": "table", "name": "users"},
            ],
            "total": 1,
        }
        resp = SearchMetadataResponse.model_validate(raw)

        assert resp.total == 1
        assert len(resp.hits) == 1
        assert resp.hits[0].fully_qualified_name == "db.users"

    def test_parse_empty_results(self) -> None:
        """Empty results produce empty hits."""
        resp = SearchMetadataResponse.model_validate({"hits": [], "total": 0})
        assert resp.total == 0
        assert resp.hits == []

    def test_extra_fields_preserved(self) -> None:
        """Extra server fields are silently accepted."""
        raw = {"hits": [], "total": 0, "took_ms": 42, "aggregations": {}}
        resp = SearchMetadataResponse.model_validate(raw)
        assert resp.total == 0


class TestGetEntityDetailsResponse:
    """Tests for GetEntityDetailsResponse parsing."""

    def test_parse_happy_path(self) -> None:
        """Parse a full entity response."""
        raw = {
            "id": "abc-123",
            "name": "users",
            "fullyQualifiedName": "pg.public.users",
            "entityType": "table",
            "description": "User accounts table",
            "owners": [{"name": "admin"}],
            "tags": [{"tagFQN": "PII.Sensitive"}],
            "columns": [{"name": "email", "dataType": "VARCHAR"}],
        }
        resp = GetEntityDetailsResponse.model_validate(raw)

        assert resp.id == "abc-123"
        assert resp.fully_qualified_name == "pg.public.users"
        assert len(resp.tags) == 1
        assert len(resp.columns) == 1

    def test_minimal_response(self) -> None:
        """Response with only optional fields missing."""
        resp = GetEntityDetailsResponse.model_validate({})

        assert resp.id is None
        assert resp.owners == []
        assert resp.tags == []
        assert resp.columns == []


class TestGetEntityLineageResponse:
    """Tests for GetEntityLineageResponse parsing."""

    def test_parse_with_edges(self) -> None:
        """Parse lineage with nodes and edges."""
        raw = {
            "entity": {"id": "1", "name": "users", "fullyQualifiedName": "db.users"},
            "nodes": [{"id": "2", "name": "orders"}],
            "edges": [{"fromEntity": "1", "toEntity": "2"}],
        }
        resp = GetEntityLineageResponse.model_validate(raw)

        assert resp.entity is not None
        assert resp.entity.name == "users"
        assert len(resp.nodes) == 1
        assert len(resp.edges) == 1


class TestCreateGlossaryResponse:
    """Tests for CreateGlossaryResponse parsing."""

    def test_parse_happy_path(self) -> None:
        """Parse a created glossary."""
        raw = {
            "id": "gl-1",
            "name": "Governance",
            "fullyQualifiedName": "Governance",
            "description": "Core governance glossary",
        }
        resp = CreateGlossaryResponse.model_validate(raw)

        assert resp.name == "Governance"
        assert resp.fully_qualified_name == "Governance"


class TestPatchEntityResponse:
    """Tests for PatchEntityResponse parsing."""

    def test_parse_with_tags(self) -> None:
        """Parse a patched entity with tags."""
        raw = {
            "id": "tbl-1",
            "name": "users",
            "fullyQualifiedName": "db.users",
            "entityType": "table",
            "tags": [{"tagFQN": "PII.Sensitive", "source": "Manual"}],
        }
        resp = PatchEntityResponse.model_validate(raw)

        assert len(resp.tags) == 1
        assert resp.entity_type == "table"


# =============================================================================
# Typed wrapper function tests
# =============================================================================


class TestSearchMetadataTyped:
    """Tests for search_metadata_typed wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_happy_path(self, mock_call: Any) -> None:
        """Params are serialized, call_tool called, response parsed."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.return_value = {
            "hits": [{"fullyQualifiedName": "db.users", "entityType": "table"}],
            "total": 1,
        }
        params = SearchMetadataParams(query="users", entity_type="table", size=5)
        result = search_metadata_typed(params)

        mock_call.assert_called_once_with(
            "search_metadata",
            {"query": "users", "entityType": "table", "size": 5, "from": 0,
             "includeDeleted": False, "includeAggregations": False},
        )
        assert isinstance(result, SearchMetadataResponse)
        assert result.total == 1
        assert result.hits[0].fully_qualified_name == "db.users"

    @patch("copilot.clients.om_mcp.call_tool")
    def test_empty_results(self, mock_call: Any) -> None:
        """Empty results from server produce empty response."""
        from copilot.clients.om_mcp import search_metadata_typed

        mock_call.return_value = {"hits": [], "total": 0}
        params = SearchMetadataParams(query="nonexistent")
        result = search_metadata_typed(params)

        assert result.total == 0
        assert result.hits == []


class TestGetEntityDetailsTyped:
    """Tests for get_entity_details_typed wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_happy_path(self, mock_call: Any) -> None:
        """Full entity details returned and parsed."""
        from copilot.clients.om_mcp import get_entity_details_typed

        mock_call.return_value = {
            "id": "abc",
            "name": "users",
            "fullyQualifiedName": "pg.public.users",
            "entityType": "table",
            "columns": [{"name": "email"}],
        }
        params = GetEntityDetailsParams(entity_type="table", fqn="pg.public.users")
        result = get_entity_details_typed(params)

        mock_call.assert_called_once_with(
            "get_entity_details",
            {"entityType": "table", "fqn": "pg.public.users"},
        )
        assert isinstance(result, GetEntityDetailsResponse)
        assert result.fully_qualified_name == "pg.public.users"


class TestGetEntityLineageTyped:
    """Tests for get_entity_lineage_typed wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_happy_path(self, mock_call: Any) -> None:
        """Lineage graph returned and parsed."""
        from copilot.clients.om_mcp import get_entity_lineage_typed

        mock_call.return_value = {
            "entity": {"id": "1", "name": "users"},
            "nodes": [],
            "edges": [],
        }
        params = GetEntityLineageParams(entity_type="table", fqn="db.users")
        result = get_entity_lineage_typed(params)

        mock_call.assert_called_once_with(
            "get_entity_lineage",
            {"entityType": "table", "fqn": "db.users", "upstreamDepth": 3, "downstreamDepth": 3},
        )
        assert isinstance(result, GetEntityLineageResponse)


class TestCreateGlossaryTyped:
    """Tests for create_glossary_typed wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_happy_path(self, mock_call: Any) -> None:
        """Glossary created and response parsed."""
        from copilot.clients.om_mcp import create_glossary_typed

        mock_call.return_value = {
            "id": "gl-1",
            "name": "Governance",
            "fullyQualifiedName": "Governance",
        }
        params = CreateGlossaryParams(name="Governance", description="Test")
        result = create_glossary_typed(params)

        assert isinstance(result, CreateGlossaryResponse)
        assert result.name == "Governance"


class TestCreateGlossaryTermTyped:
    """Tests for create_glossary_term_typed wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_happy_path(self, mock_call: Any) -> None:
        """Glossary term created and response parsed."""
        from copilot.clients.om_mcp import create_glossary_term_typed

        mock_call.return_value = {
            "id": "gt-1",
            "name": "PII",
            "fullyQualifiedName": "Governance.PII",
            "glossary": {"name": "Governance"},
        }
        params = CreateGlossaryTermParams(
            glossary="Governance",
            name="PII",
            description="Personally Identifiable Information",
        )
        result = create_glossary_term_typed(params)

        assert isinstance(result, CreateGlossaryTermResponse)
        assert result.fully_qualified_name == "Governance.PII"


class TestPatchEntityTyped:
    """Tests for patch_entity_typed wrapper."""

    @patch("copilot.clients.om_mcp.call_tool")
    def test_happy_path(self, mock_call: Any) -> None:
        """Entity patched and response parsed."""
        from copilot.clients.om_mcp import patch_entity_typed

        mock_call.return_value = {
            "id": "tbl-1",
            "name": "users",
            "fullyQualifiedName": "db.users",
            "tags": [{"tagFQN": "PII.Sensitive"}],
        }
        params = PatchEntityParams(
            entity_type="table",
            fqn="db.users",
            patch='[{"op": "add", "path": "/tags/0", "value": {"tagFQN": "PII.Sensitive"}}]',
        )
        result = patch_entity_typed(params)

        mock_call.assert_called_once_with(
            "patch_entity",
            {
                "entityType": "table",
                "fqn": "db.users",
                "patch": '[{"op": "add", "path": "/tags/0", "value": {"tagFQN": "PII.Sensitive"}}]',
            },
        )
        assert isinstance(result, PatchEntityResponse)
        assert len(result.tags) == 1
