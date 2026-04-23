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
"""Tests for scripts/load_seed.py — loader logic without a live OM instance.

Mocks urllib to verify the script sends correct API requests.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


class TestLoadSeedImport:
    def test_load_seed_module_importable(self):
        import load_seed  # type: ignore[import-not-found]

        assert hasattr(load_seed, "main")
        assert hasattr(load_seed, "SEED_FILE")

    def test_seed_file_path_is_correct(self):
        import load_seed

        expected = ROOT / "seed" / "customer_db.json"
        assert expected == load_seed.SEED_FILE

    def test_seed_file_exists(self):
        import load_seed

        assert load_seed.SEED_FILE.exists(), "seed/customer_db.json must exist"


class TestBuildColumnPayload:
    def test_basic_column(self):
        import load_seed

        result = load_seed._build_column_payload(
            {"name": "id", "dataType": "INT", "description": "Primary key"}
        )
        assert result["name"] == "id"
        assert result["dataType"] == "INT"
        assert result["description"] == "Primary key"
        assert "tags" not in result

    def test_column_with_pii_tags(self):
        import load_seed

        result = load_seed._build_column_payload(
            {
                "name": "email",
                "dataType": "VARCHAR",
                "description": "Email",
                "tags": ["PII.Sensitive"],
            }
        )
        assert result["name"] == "email"
        assert result["dataLength"] == 255
        assert len(result["tags"]) == 1
        assert result["tags"][0]["tagFQN"] == "PII.Sensitive"
        assert result["tags"][0]["source"] == "Classification"

    def test_varchar_respects_explicit_data_length(self):
        import load_seed

        result = load_seed._build_column_payload(
            {"name": "code", "dataType": "VARCHAR", "dataLength": 32}
        )
        assert result["dataLength"] == 32

    def test_type_specific_defaults(self):
        import load_seed

        assert (
            load_seed._build_column_payload({"name": "c", "dataType": "CHAR"})["dataLength"] == 36
        )
        assert (
            load_seed._build_column_payload({"name": "b", "dataType": "BINARY"})["dataLength"] == 16
        )
        assert (
            load_seed._build_column_payload({"name": "v", "dataType": "VARBINARY"})["dataLength"]
            == 255
        )
        assert (
            load_seed._build_column_payload({"name": "t", "dataType": "TEXT"})["dataLength"]
            == 65535
        )

    def test_int_has_no_data_length(self):
        import load_seed

        result = load_seed._build_column_payload({"name": "id", "dataType": "INT"})
        assert "dataLength" not in result

    def test_seed_string_columns_get_data_length_in_payload(self):
        import load_seed

        seed = json.loads(load_seed.SEED_FILE.read_text(encoding="utf-8"))
        needs = load_seed._NEEDS_DATA_LENGTH
        for table in seed["tables"]:
            for col in table["columns"]:
                payload = load_seed._build_column_payload(col)
                dt = str(payload.get("dataType", "")).upper()
                if dt in needs:
                    msg = f"{table['name']}.{col['name']}: missing dataLength for {dt}"
                    assert "dataLength" in payload, msg
                    assert payload["dataLength"] is not None, msg

    def test_column_without_description(self):
        import load_seed

        result = load_seed._build_column_payload({"name": "x", "dataType": "INT"})
        assert result["name"] == "x"
        assert "description" not in result or result.get("description") == ""


class TestGetHeaders:
    def test_headers_with_token(self):
        import load_seed

        headers = load_seed._get_headers("my-token")
        assert headers["Authorization"] == "Bearer my-token"
        assert headers["Content-Type"] == "application/json"

    def test_headers_without_token(self):
        import load_seed

        headers = load_seed._get_headers("")
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"


class TestMainExitCodes:
    @patch("load_seed.SEED_FILE", Path("/nonexistent/path/customer_db.json"))
    def test_missing_seed_file_returns_1(self):
        import load_seed

        with patch("sys.argv", ["load_seed.py"]):
            result = load_seed.main()
        assert result == 1
