#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Tests for scripts/smoke_test.py without a live backend."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _urlopen_context(payload: dict[str, Any]) -> Any:
    from unittest.mock import MagicMock

    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")

    context = MagicMock()
    context.__enter__.return_value = response
    context.__exit__.return_value = False
    return context


class TestCheckChat:
    def test_accepts_any_successful_audit_entry(self):
        import smoke_test  # type: ignore[import-not-found]

        payload = {
            "request_id": "req-1",
            "response": "Found matching tables.",
            "audit_log": [{"tool_name": "semantic_search", "success": True}],
        }

        with patch("smoke_test.urllib.request.urlopen", return_value=_urlopen_context(payload)):
            assert smoke_test.check_chat("http://127.0.0.1:8000/api/v1/chat") is True

    def test_rejects_missing_successful_audit_entry(self):
        import smoke_test

        payload = {
            "request_id": "req-2",
            "response": "Found matching tables.",
            "audit_log": [{"tool_name": "semantic_search", "success": False}],
        }

        with patch("smoke_test.urllib.request.urlopen", return_value=_urlopen_context(payload)):
            assert smoke_test.check_chat("http://127.0.0.1:8000/api/v1/chat") is False

    def test_rejects_prints_diagnostic_hint(self, capsys):
        import smoke_test

        payload = {
            "request_id": "req-3",
            "response": "Some reply.",
            "audit_log": [
                {
                    "tool_name": "search_metadata",
                    "success": False,
                    "error_code": "om_unavailable",
                }
            ],
        }

        with patch("smoke_test.urllib.request.urlopen", return_value=_urlopen_context(payload)):
            assert smoke_test.check_chat("http://127.0.0.1:8000/api/v1/chat") is False

        err = capsys.readouterr().err
        assert "HINT:" in err
        assert "trigger_om_search_reindex" in err
