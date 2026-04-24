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
"""Unit tests for NL query routing matrix (src/copilot/services/nl_router.py).

Per issue #82: representative NL queries must hit the correct MCP tool.

Tests cover:
  - Search queries → search_metadata
  - Entity detail queries → get_entity_details
  - Lineage queries → get_entity_lineage
  - Semantic / conceptual queries → semantic_search
  - RCA queries → root_cause_analysis
  - FQN extraction
  - Edge cases (empty input, ambiguous)
"""

from __future__ import annotations

import os

# Set safe defaults BEFORE any app import
os.environ.setdefault("AI_SDK_TOKEN", "test-token-placeholder-not-real-jwt")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder-not-real-key")
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "warning")

import pytest

from copilot.services.nl_router import ToolRoute, route_query

# ---------------------------------------------------------------------------
# Search → search_metadata
# ---------------------------------------------------------------------------


class TestSearchRouting:
    """NL queries that should route to search_metadata."""

    @pytest.mark.parametrize(
        "query",
        [
            "Show me all customer tables",
            "List tables in BigQuery",
            "Find tables with PII tags",
            "Show me tier 1 tables",
            "How many tables in production?",
            "Tables owned by the data-eng team",
        ],
    )
    def test_search_queries_route_to_search_metadata(self, query: str) -> None:
        result = route_query(query, intent="search")
        assert result is not None
        assert result.tool_name == "search_metadata"

    def test_search_query_includes_user_text(self) -> None:
        result = route_query("Show me tier 1 tables", intent="search")
        assert result is not None
        assert result.arguments["query"] == "Show me tier 1 tables"


# ---------------------------------------------------------------------------
# Entity details → get_entity_details
# ---------------------------------------------------------------------------


class TestDetailsRouting:
    """NL queries that should route to get_entity_details."""

    @pytest.mark.parametrize(
        "query",
        [
            "Tell me about the orders table",
            "What is dim_customers?",
            "Describe the users table",
            "Show me details of customer_db.public.orders",
            "Show details for the payments table",
            "Info on the transactions table",
        ],
    )
    def test_details_queries_route_to_get_entity_details(self, query: str) -> None:
        result = route_query(query)
        assert result is not None
        assert result.tool_name == "get_entity_details"

    def test_extracts_fqn_from_details_query(self) -> None:
        result = route_query("Tell me about customer_db.public.orders")
        assert result is not None
        assert result.tool_name == "get_entity_details"
        assert result.arguments.get("fqn") == "customer_db.public.orders"

    def test_extracts_simple_name_from_details_query(self) -> None:
        result = route_query("Tell me about dim_customers")
        assert result is not None
        assert result.tool_name == "get_entity_details"
        assert result.arguments.get("fqn") == "dim_customers"

    def test_what_is_extracts_name(self) -> None:
        result = route_query("What is dim_customers?")
        assert result is not None
        assert result.tool_name == "get_entity_details"

    def test_what_are_the_columns_routes_to_details(self) -> None:
        result = route_query("What are the columns of the orders table?")
        assert result is not None
        assert result.tool_name == "get_entity_details"


# ---------------------------------------------------------------------------
# Lineage → get_entity_lineage
# ---------------------------------------------------------------------------


class TestLineageRouting:
    """NL queries that should route to get_entity_lineage."""

    @pytest.mark.parametrize(
        "query",
        [
            "Show me the lineage of the orders table",
            "What depends on customer_db.public.users?",
            "What are the upstream dependencies of dim_orders?",
            "Show downstream impact of raw_events",
            "Trace back data for the revenue table",
            "What feeds into the analytics pipeline?",
            "What flows from the customers table?",
        ],
    )
    def test_lineage_queries_route_to_get_entity_lineage(self, query: str) -> None:
        result = route_query(query)
        assert result is not None
        assert result.tool_name == "get_entity_lineage"

    def test_lineage_extracts_fqn(self) -> None:
        result = route_query("What depends on customer_db.public.users?")
        assert result is not None
        assert result.arguments.get("fqn") == "customer_db.public.users"

    def test_lineage_intent_override(self) -> None:
        """Even without keyword match, intent=lineage forces lineage routing."""
        result = route_query("Show me the graph for orders", intent="lineage")
        assert result is not None
        assert result.tool_name == "get_entity_lineage"


# ---------------------------------------------------------------------------
# Semantic search → semantic_search
# ---------------------------------------------------------------------------


class TestSemanticSearchRouting:
    """NL queries that should route to semantic_search."""

    @pytest.mark.parametrize(
        "query",
        [
            "Find tables related to customer purchase behavior",
            "Tables about revenue patterns",
            "Find something about user engagement",
            "Data similar to marketing campaigns",
        ],
    )
    def test_semantic_queries_route_to_semantic_search(self, query: str) -> None:
        result = route_query(query)
        assert result is not None
        assert result.tool_name == "semantic_search"

    def test_semantic_query_includes_full_text(self) -> None:
        result = route_query("Tables about revenue patterns")
        assert result is not None
        assert result.arguments["query"] == "Tables about revenue patterns"


# ---------------------------------------------------------------------------
# Root cause analysis → root_cause_analysis
# ---------------------------------------------------------------------------


class TestRcaRouting:
    """NL queries that should route to root_cause_analysis."""

    @pytest.mark.parametrize(
        "query",
        [
            "What's broken in the pipeline?",
            "Root cause analysis for data quality issues",
            "Why is the orders table failing?",
            "Data quality issue with the users table",
        ],
    )
    def test_rca_queries_route_to_root_cause_analysis(self, query: str) -> None:
        result = route_query(query)
        assert result is not None
        assert result.tool_name == "root_cause_analysis"

    def test_rca_intent_override(self) -> None:
        result = route_query("Check the orders pipeline", intent="rca")
        assert result is not None
        assert result.tool_name == "root_cause_analysis"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_input_returns_none(self) -> None:
        assert route_query("") is None
        assert route_query("  ") is None

    def test_returns_tool_route_dataclass(self) -> None:
        result = route_query("Show me tables", intent="search")
        assert isinstance(result, ToolRoute)

    def test_default_search_for_ambiguous_query(self) -> None:
        """Ambiguous queries with search intent default to search_metadata."""
        result = route_query("tables", intent="search")
        assert result is not None
        assert result.tool_name == "search_metadata"

    def test_classify_intent_falls_through(self) -> None:
        """Classify intent is not handled by the router → returns None."""
        result = route_query("Auto-classify PII columns in customer_db", intent="classify")
        assert result is None

    def test_glossary_intent_falls_through(self) -> None:
        """Glossary intent is not handled by the router → returns None."""
        result = route_query("Create a glossary for data terms", intent="glossary")
        assert result is None


# ---------------------------------------------------------------------------
# Integration: routing matrix from NLQueryEngine.md
# ---------------------------------------------------------------------------


class TestNLQueryEngineMatrix:
    """Verifies the full routing matrix from NLQueryEngine.md test cases."""

    def test_show_tier_1_tables(self) -> None:
        """Test case 1: 'Show me tier 1 tables' → search_metadata."""
        result = route_query("Show me tier 1 tables")
        assert result is not None
        assert result.tool_name == "search_metadata"

    def test_tables_about_revenue(self) -> None:
        """Test case 2: 'Tables about revenue' → semantic_search."""
        result = route_query("Tables about revenue")
        assert result is not None
        assert result.tool_name == "semantic_search"

    def test_what_is_dim_customers(self) -> None:
        """Test case 3: 'What is dim_customers?' → get_entity_details."""
        result = route_query("What is dim_customers?")
        assert result is not None
        assert result.tool_name == "get_entity_details"

    def test_show_all_tables_owned_by_team(self) -> None:
        """NLQueryEngine.md example 1: search by owner."""
        result = route_query("Show me all tables owned by the data-eng team")
        assert result is not None
        assert result.tool_name == "search_metadata"

    def test_find_tables_related_to_concept(self) -> None:
        """NLQueryEngine.md example 2: conceptual search."""
        result = route_query("Find tables related to customer purchase behavior")
        assert result is not None
        assert result.tool_name == "semantic_search"

    def test_tell_me_about_orders_table(self) -> None:
        """NLQueryEngine.md example 3: entity details."""
        result = route_query("Tell me about the orders table")
        assert result is not None
        assert result.tool_name == "get_entity_details"
