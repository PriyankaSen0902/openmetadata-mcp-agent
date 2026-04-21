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
"""Typed Pydantic v2 wrappers for the top 6 MCP tools.

Per issue #22 (P1-09): raw ``call_tool`` returns untyped dicts.  These models
validate inputs **before** the SDK call and parse responses **after**, catching
bugs at the boundary instead of deep inside business logic.

Schemas sourced from:
  - ``.idea/Plan/DataFindings/ExistingMCPAudit.md`` (canonical reference)
  - ``openmetadata-mcp/src/main/resources/json/data/mcp/tools.json``

Design rules:
  - Params: strict validation (``extra="forbid"``), snake_case fields with
    camelCase ``alias`` for SDK serialization.
  - Response: permissive (``extra="allow"``) because OM server may add fields.
  - All models use ``populate_by_name=True`` so callers can use snake_case.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Shared base classes
# =============================================================================


class _StrictParams(BaseModel):
    """Base for all Params models — strict, aliased, no extras."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        frozen=True,
    )


class _PermissiveResponse(BaseModel):
    """Base for all Response models — permissive to tolerate OM server changes."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )


# =============================================================================
# Tool 1: search_metadata
# =============================================================================


class SearchMetadataParams(_StrictParams):
    """Input parameters for the ``search_metadata`` MCP tool.

    All parameters are optional — calling with no args returns the first page
    of all entities.
    """

    query: str | None = Field(
        default=None,
        description="Natural language or keyword search query.",
    )
    entity_type: str | None = Field(
        default=None,
        alias="entityType",
        description="Filter by entity type (singular): table, dashboard, topic, etc.",
    )
    query_filter: str | None = Field(
        default=None,
        alias="queryFilter",
        description="Advanced OpenSearch JSON query string. Overrides ``query``.",
    )
    from_: int = Field(
        default=0,
        ge=0,
        alias="from",
        description="Pagination offset.",
    )
    size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Results per page (max 50).",
    )
    include_deleted: bool = Field(
        default=False,
        alias="includeDeleted",
        description="Include soft-deleted entities.",
    )
    fields: str | None = Field(
        default=None,
        description="Comma-separated additional fields (e.g. 'columns,queries').",
    )
    include_aggregations: bool = Field(
        default=False,
        alias="includeAggregations",
        description="Include facet aggregations in response.",
    )
    max_aggregation_buckets: int | None = Field(
        default=None,
        ge=1,
        le=50,
        alias="maxAggregationBuckets",
        description="Max aggregation buckets (max 50).",
    )


class SearchHit(_PermissiveResponse):
    """A single search result entry."""

    fully_qualified_name: str | None = Field(
        default=None,
        alias="fullyQualifiedName",
    )
    entity_type: str | None = Field(
        default=None,
        alias="entityType",
    )
    name: str | None = None
    description: str | None = None
    display_name: str | None = Field(default=None, alias="displayName")


class SearchMetadataResponse(_PermissiveResponse):
    """Parsed response from ``search_metadata``.

    The OM server returns search hits under various keys depending on the
    query.  We capture the common pattern.
    """

    hits: list[SearchHit] = Field(default_factory=list)
    total: int = Field(default=0)


# =============================================================================
# Tool 2: get_entity_details
# =============================================================================


class GetEntityDetailsParams(_StrictParams):
    """Input parameters for the ``get_entity_details`` MCP tool."""

    entity_type: str = Field(
        ...,
        alias="entityType",
        description="Type of entity: table, dashboard, topic, pipeline, etc.",
    )
    fqn: str = Field(
        ...,
        description="Fully qualified name of the entity.",
    )


class GetEntityDetailsResponse(_PermissiveResponse):
    """Parsed response from ``get_entity_details``.

    Contains full entity details.  We validate the minimum set of fields we
    use; additional server fields are captured by ``extra='allow'``.
    """

    id: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = Field(
        default=None,
        alias="fullyQualifiedName",
    )
    entity_type: str | None = Field(
        default=None,
        alias="entityType",
    )
    description: str | None = None
    owners: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Tool 3: get_entity_lineage
# =============================================================================


class GetEntityLineageParams(_StrictParams):
    """Input parameters for the ``get_entity_lineage`` MCP tool."""

    entity_type: str = Field(
        ...,
        alias="entityType",
        description="Type of entity.",
    )
    fqn: str = Field(
        ...,
        description="Fully qualified name of the entity.",
    )
    upstream_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="upstreamDepth",
        description="Upstream hops to traverse (max 10).",
    )
    downstream_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="downstreamDepth",
        description="Downstream hops to traverse (max 10).",
    )


class LineageEdge(_PermissiveResponse):
    """A single lineage edge between two nodes."""

    from_entity: str | None = Field(default=None, alias="fromEntity")
    to_entity: str | None = Field(default=None, alias="toEntity")


class LineageNodeInfo(_PermissiveResponse):
    """A node in the lineage graph."""

    id: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = Field(
        default=None,
        alias="fullyQualifiedName",
    )
    entity_type: str | None = Field(
        default=None,
        alias="entityType",
    )


class GetEntityLineageResponse(_PermissiveResponse):
    """Parsed response from ``get_entity_lineage``."""

    entity: LineageNodeInfo | None = None
    nodes: list[LineageNodeInfo] = Field(default_factory=list)
    edges: list[LineageEdge] = Field(default_factory=list)
    upstream_edges: list[LineageEdge] = Field(
        default_factory=list,
        alias="upstreamEdges",
    )
    downstream_edges: list[LineageEdge] = Field(
        default_factory=list,
        alias="downstreamEdges",
    )


# =============================================================================
# Tool 4: create_glossary
# =============================================================================


class CreateGlossaryParams(_StrictParams):
    """Input parameters for the ``create_glossary`` MCP tool."""

    name: str = Field(
        ...,
        min_length=1,
        description="Glossary name.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Glossary description.",
    )
    mutually_exclusive: bool = Field(
        default=False,
        alias="mutuallyExclusive",
        description="Whether child terms are mutually exclusive.",
    )
    owners: list[str] | None = Field(
        default=None,
        description="OM User or Team names.",
    )
    reviewers: list[str] | None = Field(
        default=None,
        description="OM User or Team names for approval workflow.",
    )


class CreateGlossaryResponse(_PermissiveResponse):
    """Parsed response from ``create_glossary``."""

    id: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = Field(
        default=None,
        alias="fullyQualifiedName",
    )
    description: str | None = None


# =============================================================================
# Tool 5: create_glossary_term
# =============================================================================


class CreateGlossaryTermParams(_StrictParams):
    """Input parameters for the ``create_glossary_term`` MCP tool."""

    glossary: str = Field(
        ...,
        min_length=1,
        description="Parent glossary FQN.",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Term name.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Term description.",
    )
    parent_term: str | None = Field(
        default=None,
        alias="parentTerm",
        description="Parent term FQN for hierarchy.",
    )
    owners: list[str] | None = Field(
        default=None,
        description="OM User or Team names.",
    )
    reviewers: list[str] | None = Field(
        default=None,
        description="OM User or Team names for approval workflow.",
    )


class CreateGlossaryTermResponse(_PermissiveResponse):
    """Parsed response from ``create_glossary_term``."""

    id: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = Field(
        default=None,
        alias="fullyQualifiedName",
    )
    glossary: dict[str, Any] | None = None
    description: str | None = None


# =============================================================================
# Tool 6: patch_entity
# =============================================================================


class PatchEntityParams(_StrictParams):
    """Input parameters for the ``patch_entity`` MCP tool.

    ``patch`` is a JSONPatch (RFC 6902) operations string.  The OM server
    expects it as a JSON-encoded string, not a parsed list.
    """

    entity_type: str = Field(
        ...,
        alias="entityType",
        description="Entity type to patch.",
    )
    fqn: str = Field(
        ...,
        description="Fully qualified name of the entity.",
    )
    patch: str = Field(
        ...,
        min_length=2,
        description='JSONPatch operations as JSON array string (e.g. \'[{"op":"add",...}]\').',
    )


class PatchEntityResponse(_PermissiveResponse):
    """Parsed response from ``patch_entity``."""

    id: str | None = None
    name: str | None = None
    fully_qualified_name: str | None = Field(
        default=None,
        alias="fullyQualifiedName",
    )
    entity_type: str | None = Field(
        default=None,
        alias="entityType",
    )
    description: str | None = None
    tags: list[dict[str, Any]] = Field(default_factory=list)
