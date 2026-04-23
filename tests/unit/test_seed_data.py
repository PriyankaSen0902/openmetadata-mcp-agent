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
"""Tests for the frozen seed dataset (seed/customer_db.json).

Validates issue #26 (P1-13) acceptance criteria:
  - 50+ tables total
  - At least 5 tables with PII-tagged columns (target: 12)
  - 2 planted prompt-injection descriptions
  - Tier1 entries for classification demos
  - All tables have required fields
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SEED_FILE = ROOT / "seed" / "customer_db.json"


@pytest.fixture(scope="module")
def seed_data():
    assert SEED_FILE.exists(), f"Seed file not found: {SEED_FILE}"
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    assert "tables" in data, "Seed file must have a 'tables' key"
    return data


@pytest.fixture(scope="module")
def tables(seed_data):
    return seed_data["tables"]


class TestSeedStructure:
    def test_seed_has_database_and_schema(self, seed_data):
        assert seed_data.get("database") == "customer_db"
        assert seed_data.get("schema") == "public"

    def test_minimum_table_count(self, tables):
        assert len(tables) >= 50, f"Expected 50+ tables, got {len(tables)}"

    def test_all_tables_have_name(self, tables):
        for table in tables:
            assert "name" in table, f"Table missing 'name': {table}"
            assert isinstance(table["name"], str)
            assert len(table["name"]) > 0

    def test_all_tables_have_columns(self, tables):
        for table in tables:
            assert "columns" in table, f"Table '{table['name']}' missing 'columns'"
            assert len(table["columns"]) > 0, f"Table '{table['name']}' has no columns"

    def test_all_columns_have_required_fields(self, tables):
        for table in tables:
            for col in table["columns"]:
                assert "name" in col, f"Column in '{table['name']}' missing 'name'"
                assert "dataType" in col, (
                    f"Column '{col['name']}' in '{table['name']}' missing 'dataType'"
                )

    def test_unique_table_names(self, tables):
        names = [t["name"] for t in tables]
        assert len(names) == len(set(names)), f"Duplicate table names found: {names}"


class TestPiiTables:
    def _pii_tables(self, tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [t for t in tables if any(tag for c in t["columns"] for tag in c.get("tags", []))]

    def test_minimum_pii_table_count(self, tables):
        pii = self._pii_tables(tables)
        assert len(pii) >= 5, f"Expected at least 5 PII tables, got {len(pii)}"

    def test_target_pii_table_count(self, tables):
        pii = self._pii_tables(tables)
        assert len(pii) >= 12, f"Expected 12 PII tables per spec, got {len(pii)}"

    def test_pii_tags_are_valid(self, tables):
        for table in tables:
            for col in table["columns"]:
                for tag in col.get("tags", []):
                    assert "PII" in tag, (
                        f"Tag '{tag}' on '{table['name']}.{col['name']}' doesn't contain 'PII'"
                    )


class TestPromptInjection:
    def _injection_tables(self, tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [t for t in tables if "injection" in t.get("description", "").lower()]

    def test_two_injection_tables_exist(self, tables):
        inj = self._injection_tables(tables)
        assert len(inj) >= 2, f"Expected 2 prompt-injection tables, got {len(inj)}"

    def test_injection_has_planted_content(self, tables):
        inj = self._injection_tables(tables)
        descriptions_all = ""
        for t in inj:
            for c in t["columns"]:
                descriptions_all += c.get("description", "")

        assert "ignore" in descriptions_all.lower() or "\u200b" in descriptions_all, (
            "Prompt-injection tables should contain injection patterns in column descriptions"
        )


class TestTierClassification:
    def test_tier1_table_exists(self, tables):
        tier1 = [t for t in tables if t.get("tier") == "Tier1"]
        assert len(tier1) >= 1, "Expected at least 1 Tier1 table for classification demos"
