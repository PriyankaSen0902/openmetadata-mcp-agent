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
"""Unit tests for drift detection pure logic (src/copilot/services/drift.py).

Tests cover:
  - Hash computation stability
  - Hash drift detection
  - Tag missing / unexpected detection
  - Edge cases: first scan (no baseline), empty entities, OM down
"""

from __future__ import annotations

import os
from typing import Any

# Set safe defaults BEFORE any app import
os.environ.setdefault("AI_SDK_TOKEN", "test-token-placeholder-not-real-jwt")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder-not-real-key")
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "warning")

from copilot.services.drift import (
    DriftSignal,
    _extract_tag_fqns,
    _hash_entity,
    detect_drift,
)

# ---------------------------------------------------------------------------
# Hash computation
# ---------------------------------------------------------------------------


class TestHashEntity:
    """Tests for _hash_entity stability and correctness."""

    def test_same_entity_produces_same_hash(self) -> None:
        entity = {
            "description": "A table",
            "columns": [
                {"name": "id", "dataType": "INT", "tags": []},
                {"name": "email", "dataType": "VARCHAR", "tags": [{"tagFQN": "PII.Sensitive"}]},
            ],
            "tags": [{"tagFQN": "Tier.Tier1"}],
        }
        assert _hash_entity(entity) == _hash_entity(entity)

    def test_column_order_does_not_affect_hash(self) -> None:
        entity_a = {
            "columns": [
                {"name": "a", "dataType": "INT", "tags": []},
                {"name": "b", "dataType": "VARCHAR", "tags": []},
            ],
        }
        entity_b = {
            "columns": [
                {"name": "b", "dataType": "VARCHAR", "tags": []},
                {"name": "a", "dataType": "INT", "tags": []},
            ],
        }
        assert _hash_entity(entity_a) == _hash_entity(entity_b)

    def test_tag_order_does_not_affect_hash(self) -> None:
        entity_a = {
            "tags": [{"tagFQN": "PII.Sensitive"}, {"tagFQN": "Tier.Tier1"}],
        }
        entity_b = {
            "tags": [{"tagFQN": "Tier.Tier1"}, {"tagFQN": "PII.Sensitive"}],
        }
        assert _hash_entity(entity_a) == _hash_entity(entity_b)

    def test_description_change_changes_hash(self) -> None:
        entity_a = {"description": "Original"}
        entity_b = {"description": "Modified"}
        assert _hash_entity(entity_a) != _hash_entity(entity_b)

    def test_tag_addition_changes_hash(self) -> None:
        entity_a: dict[str, Any] = {"tags": []}
        entity_b = {"tags": [{"tagFQN": "PII.Sensitive"}]}
        assert _hash_entity(entity_a) != _hash_entity(entity_b)

    def test_empty_entity_hashes_consistently(self) -> None:
        assert _hash_entity({}) == _hash_entity({})


# ---------------------------------------------------------------------------
# Tag extraction
# ---------------------------------------------------------------------------


class TestExtractTagFqns:
    """Tests for _extract_tag_fqns."""

    def test_extracts_top_level_tags(self) -> None:
        entity = {"tags": [{"tagFQN": "PII.Sensitive"}, {"tagFQN": "Tier.Tier1"}]}
        assert _extract_tag_fqns(entity) == {"PII.Sensitive", "Tier.Tier1"}

    def test_extracts_column_level_tags(self) -> None:
        entity = {
            "columns": [
                {"name": "email", "tags": [{"tagFQN": "PII.Sensitive"}]},
                {"name": "id", "tags": []},
            ],
        }
        assert _extract_tag_fqns(entity) == {"PII.Sensitive"}

    def test_combines_top_and_column_tags(self) -> None:
        entity = {
            "tags": [{"tagFQN": "Tier.Tier1"}],
            "columns": [
                {"name": "email", "tags": [{"tagFQN": "PII.Sensitive"}]},
            ],
        }
        assert _extract_tag_fqns(entity) == {"Tier.Tier1", "PII.Sensitive"}

    def test_empty_entity(self) -> None:
        assert _extract_tag_fqns({}) == set()


# ---------------------------------------------------------------------------
# Drift detection (pure logic)
# ---------------------------------------------------------------------------


class TestDetectDrift:
    """Tests for the detect_drift pure function."""

    def test_no_baseline_returns_empty(self) -> None:
        """First scan: no baseline hash or tags → no drift."""
        entity = {"description": "A table", "tags": [], "columns": []}
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=None,
            baseline_tags=None,
        )
        assert items == []

    def test_hash_unchanged_returns_empty(self) -> None:
        entity = {"description": "A table", "tags": [], "columns": []}
        h = _hash_entity(entity)
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=h,
            baseline_tags=set(),
        )
        assert items == []

    def test_hash_changed_returns_drift(self) -> None:
        entity = {"description": "Modified", "tags": [], "columns": []}
        old_hash = _hash_entity({"description": "Original", "tags": [], "columns": []})
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=old_hash,
        )
        assert len(items) == 1
        assert items[0].signal == DriftSignal.HASH_CHANGED
        assert items[0].entity_fqn == "db.schema.table1"

    def test_governance_tag_removed_returns_tag_missing(self) -> None:
        entity: dict[str, Any] = {"tags": [], "columns": []}
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=None,
            baseline_tags={"PII.Sensitive"},
        )
        tag_missing = [i for i in items if i.signal == DriftSignal.TAG_MISSING]
        assert len(tag_missing) == 1
        assert "PII.Sensitive" in tag_missing[0].detail

    def test_governance_tag_added_returns_tag_unexpected(self) -> None:
        entity = {"tags": [{"tagFQN": "PII.Sensitive"}], "columns": []}
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=None,
            baseline_tags=set(),
        )
        tag_unexpected = [i for i in items if i.signal == DriftSignal.TAG_UNEXPECTED]
        assert len(tag_unexpected) == 1
        assert "PII.Sensitive" in tag_unexpected[0].detail

    def test_non_governance_tag_change_not_flagged(self) -> None:
        """Tags without governance prefixes should not trigger tag drift."""
        entity = {"tags": [{"tagFQN": "CustomTag.Foo"}], "columns": []}
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=None,
            baseline_tags=set(),
        )
        tag_items = [
            i for i in items if i.signal in (DriftSignal.TAG_MISSING, DriftSignal.TAG_UNEXPECTED)
        ]
        assert tag_items == []

    def test_combined_hash_and_tag_drift(self) -> None:
        """Both hash change and tag removal detected in one call."""
        old_hash = _hash_entity({"description": "Original"})
        entity = {"description": "Changed", "tags": [], "columns": []}
        items = detect_drift(
            entity_fqn="db.schema.table1",
            entity_type="table",
            current=entity,
            baseline_hash=old_hash,
            baseline_tags={"Tier.Tier1"},
        )
        signals = {i.signal for i in items}
        assert DriftSignal.HASH_CHANGED in signals
        assert DriftSignal.TAG_MISSING in signals
