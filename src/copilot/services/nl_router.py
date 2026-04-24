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
"""Deterministic NL → tool router for the governance agent.

Provides a fast-path that maps common natural-language query patterns to
the correct MCP tool *without* an LLM call.  Falls back to ``None`` when
the query is ambiguous, in which case the caller should use the LLM-based
tool selector.

Per .idea/Plan/FeatureDev/NLQueryEngine.md:
  - Keyword / filter queries → ``search_metadata``
  - "Tell me about X" / "What is X?" → ``get_entity_details``
  - "What depends on X?" / lineage / upstream / downstream → ``get_entity_lineage``
  - Conceptual / vague queries → ``semantic_search``
  - "What's broken?" / failure / root cause → ``root_cause_analysis``
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolRoute:
    """Result of deterministic routing: which tool to call and with what args."""

    tool_name: str
    arguments: dict[str, Any]
    rationale: str


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Patterns that indicate a lineage query
_LINEAGE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:lineage|upstream|downstream|depends?\s+on|impact|dependen)\b", re.I),
    re.compile(r"\bwhat\s+(?:feeds?|flows?\s+(?:into|from)|sources?)\b", re.I),
    re.compile(r"\b(?:trace|track)\s+(?:back|forward|data)\b", re.I),
]

# Patterns that indicate entity details
_DETAILS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:tell\s+me\s+about|describe|show\s+(?:me\s+)?details?\s+(?:of|for|about)?|"
        r"what\s+is|what\s+are\s+the\s+columns?\s+(?:of|in|for)|"
        r"explain|info\s+(?:on|about|for))\b",
        re.I,
    ),
]

# Patterns that indicate root cause analysis
_RCA_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:root\s+cause|what(?:'s|s|\s+is)\s+broken|why\s+(?:is|did|are)|"
        r"failure|failed|data\s+quality\s+(?:issue|problem|error))\b",
        re.I,
    ),
]

# Patterns that indicate semantic / conceptual search (vague, no keywords)
_SEMANTIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:related\s+to|similar\s+to|about|like|concept|meaning)\b",
        re.I,
    ),
    re.compile(r"\btables?\s+(?:about|related\s+to|like)\b", re.I),
    re.compile(r"\bfind\s+(?:something|anything|data)\s+(?:about|related|similar)\b", re.I),
]

# Patterns that extract a FQN-like entity reference
_FQN_PATTERN = re.compile(
    r"(?:^|\s)([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*){1,4})(?:\s|$|[?.,!])",
)

# Pattern to extract a simple entity name (non-FQN)
_ENTITY_NAME_PATTERN = re.compile(
    r"(?:tell\s+me\s+about|describe|what\s+is|details?\s+(?:of|for|about)?|"
    r"info\s+(?:on|about|for)|show\s+(?:me\s+)?)\s+(?:the\s+)?([a-zA-Z_]\w*(?:[_-]\w+)*)",
    re.I,
)


def _extract_entity_ref(message: str) -> str | None:
    """Try to extract a FQN or entity name from the message."""
    # First try FQN (e.g., customer_db.public.orders)
    m = _FQN_PATTERN.search(message)
    if m:
        return m.group(1)

    # Fall back to a simple name reference
    m = _ENTITY_NAME_PATTERN.search(message)
    if m:
        return m.group(1)

    return None


def _any_match(patterns: list[re.Pattern[str]], text: str) -> bool:
    """Return True if any pattern matches the text."""
    return any(p.search(text) for p in patterns)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def route_query(message: str, intent: str | None = None) -> ToolRoute | None:
    """Attempt deterministic routing of a NL query to a tool.

    Args:
        message: The user's natural-language message.
        intent: Optional pre-classified intent (from classify_intent node).

    Returns:
        A ``ToolRoute`` if a deterministic match is found, else ``None``
        (caller should fall back to LLM-based tool selection).
    """
    text = message.strip()
    if not text:
        return None

    # 1. Lineage queries — check first because they're unambiguous
    if intent == "lineage" or _any_match(_LINEAGE_PATTERNS, text):
        entity = _extract_entity_ref(text)
        args: dict[str, Any] = {}
        if entity:
            args["fqn"] = entity
            args["entity_type"] = "table"
        return ToolRoute(
            tool_name="get_entity_lineage",
            arguments=args,
            rationale="Query matches lineage pattern (upstream/downstream/depends)",
        )

    # 2. RCA queries
    if intent == "rca" or _any_match(_RCA_PATTERNS, text):
        return ToolRoute(
            tool_name="root_cause_analysis",
            arguments={},
            rationale="Query matches root-cause-analysis pattern",
        )

    # 3. Entity details — "tell me about X", "what is X?"
    if _any_match(_DETAILS_PATTERNS, text):
        entity = _extract_entity_ref(text)
        args = {}
        if entity:
            args["fqn"] = entity
            args["entity_type"] = "table"
        return ToolRoute(
            tool_name="get_entity_details",
            arguments=args,
            rationale="Query matches entity-details pattern (tell me about / what is)",
        )

    # 4. Semantic / conceptual search
    if _any_match(_SEMANTIC_PATTERNS, text):
        return ToolRoute(
            tool_name="semantic_search",
            arguments={"query": text},
            rationale="Query is conceptual/vague — using semantic search",
        )

    # 5. Default for search intent: keyword search
    if intent in ("search", None):
        return ToolRoute(
            tool_name="search_metadata",
            arguments={"query": text},
            rationale="Default routing: keyword search via search_metadata",
        )

    # No deterministic match — let the LLM decide
    return None
