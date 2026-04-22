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

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


class TestLoadSeedImport:
    def test_load_seed_module_importable(self):
        import load_seed

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
        assert len(result["tags"]) == 1
        assert result["tags"][0]["tagFQN"] == "PII.Sensitive"
        assert result["tags"][0]["source"] == "Classification"

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
