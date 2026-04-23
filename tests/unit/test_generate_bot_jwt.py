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
"""Tests for scripts/generate_bot_jwt.py.

Mocks urllib.request.urlopen at the boundary to avoid real HTTP calls.
Tests the happy path, auth failure, bot not found, and token gen failure.
"""

from __future__ import annotations

import json
import sys
from http.client import RemoteDisconnected
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import generate_bot_jwt  # type: ignore[import-not-found]  # noqa: E402


def _mock_response(data: dict[str, Any], status: int = 200) -> MagicMock:
    """Create a mock urllib response that behaves like a context manager."""
    body = json.dumps(data).encode("utf-8")
    mock = MagicMock()
    mock.read.return_value = body
    mock.status = status
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def _mock_http_error(code: int, body: str = "") -> HTTPError:
    """Create an HTTPError with a readable body."""
    fp = BytesIO(body.encode("utf-8"))
    return HTTPError(
        url="http://localhost:8585/api/v1/test",
        code=code,
        msg=f"HTTP {code}",
        hdrs={},  # type: ignore[arg-type]
        fp=fp,
    )


class TestResolveExpiry:
    def test_exact_match_30(self) -> None:
        assert generate_bot_jwt._resolve_expiry(30) == "30"

    def test_exact_match_7(self) -> None:
        assert generate_bot_jwt._resolve_expiry(7) == "7"

    def test_exact_match_unlimited(self) -> None:
        assert generate_bot_jwt._resolve_expiry(0) == "Unlimited"

    def test_rounds_unsupported_one_day_up_to_seven(self) -> None:
        assert generate_bot_jwt._resolve_expiry(1) == "7"

    def test_rounds_to_nearest(self) -> None:
        result = generate_bot_jwt._resolve_expiry(25)
        assert result == "30"


class TestCheckHealth:
    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_healthy_server(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_response({"version": "1.6.2"})
        assert generate_bot_jwt.check_health("http://localhost:8585") is True

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_unreachable_server(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = URLError("Connection refused")
        assert generate_bot_jwt.check_health("http://localhost:8585") is False

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_remote_disconnect_is_handled(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = RemoteDisconnected(
            "Remote end closed connection without response"
        )
        assert generate_bot_jwt.check_health("http://localhost:8585") is False

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_unhealthy_payload(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_response({"status": "starting"})
        assert generate_bot_jwt.check_health("http://localhost:8585") is False


class TestLoginAdmin:
    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_successful_login(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_response({"accessToken": "admin-jwt-token-123"})
        token = generate_bot_jwt.login_admin("http://localhost:8585", "admin", "admin")
        assert token == "admin-jwt-token-123"

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_successful_login_falls_back_to_admin_email(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = [
            _mock_http_error(401, '{"message":"Unauthorized"}'),
            _mock_response({"accessToken": "admin-jwt-token-123"}),
        ]

        token = generate_bot_jwt.login_admin("http://localhost:8585", "admin", "admin")

        assert token == "admin-jwt-token-123"
        request_calls = mock_urlopen.call_args_list
        assert len(request_calls) == 2
        first_request = request_calls[0].args[0]
        second_request = request_calls[1].args[0]
        assert json.loads(first_request.data.decode("utf-8"))["email"] == "admin"
        assert json.loads(second_request.data.decode("utf-8"))["email"] == "admin@open-metadata.org"

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_login_failure_401(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = [
            _mock_http_error(401, '{"message":"Unauthorized"}'),
            _mock_http_error(401, '{"message":"Unauthorized"}'),
        ]
        token = generate_bot_jwt.login_admin("http://localhost:8585", "admin", "wrong")
        assert token is None

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_login_missing_access_token(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = [
            _mock_response({"some_other_field": "value"}),
            _mock_response({"some_other_field": "value"}),
        ]
        token = generate_bot_jwt.login_admin("http://localhost:8585", "admin", "admin")
        assert token is None

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_login_rejects_token_type_without_access_token(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = [
            _mock_response({"tokenType": "Bearer"}),
            _mock_response({"tokenType": "Bearer"}),
        ]
        token = generate_bot_jwt.login_admin("http://localhost:8585", "admin", "admin")
        assert token is None


class TestGetBotUser:
    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_bot_found(self, mock_urlopen: MagicMock) -> None:
        bot_response = _mock_response(
            {
                "name": "ingestion-bot",
                "botUser": {"id": "user-uuid-123", "name": "ingestion-bot"},
            }
        )
        user_response = _mock_response(
            {"id": "user-uuid-123", "name": "ingestion-bot", "email": "ingestion-bot"}
        )
        mock_urlopen.side_effect = [bot_response, user_response]

        result = generate_bot_jwt.get_bot_user("http://localhost:8585", "admin-token")
        assert result is not None
        assert result["id"] == "user-uuid-123"

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_bot_not_found_404(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = _mock_http_error(404, '{"message":"Not found"}')
        result = generate_bot_jwt.get_bot_user("http://localhost:8585", "admin-token")
        assert result is None


class TestGenerateToken:
    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_token_generated(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_response({"JWTToken": "generated-bot-jwt-token-xyz"})

        user_data = {"id": "user-uuid-123", "name": "ingestion-bot"}
        token = generate_bot_jwt.generate_token(
            "http://localhost:8585", "admin-token", user_data, "30"
        )
        assert token == "generated-bot-jwt-token-xyz"

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_token_generation_failure(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = _mock_http_error(500, '{"message":"Server error"}')

        user_data = {"id": "user-uuid-123", "name": "ingestion-bot"}
        token = generate_bot_jwt.generate_token(
            "http://localhost:8585", "admin-token", user_data, "30"
        )
        assert token is None

    @patch("generate_bot_jwt.urllib.request.urlopen")
    def test_token_accepts_token_alias_field(self, mock_urlopen: MagicMock) -> None:
        """Some OM responses use ``token`` instead of ``JWTToken``."""
        mock_urlopen.return_value = _mock_response({"token": "token-from-alias"})

        user_data = {"id": "user-uuid-123", "name": "ingestion-bot"}
        token = generate_bot_jwt.generate_token(
            "http://localhost:8585", "admin-token", user_data, "30"
        )
        assert token == "token-from-alias"


class TestMain:
    @patch("generate_bot_jwt.generate_token")
    @patch("generate_bot_jwt.get_bot_user")
    @patch("generate_bot_jwt.login_admin")
    @patch("generate_bot_jwt.check_health")
    def test_happy_path(
        self,
        mock_health: MagicMock,
        mock_login: MagicMock,
        mock_bot_user: MagicMock,
        mock_gen_token: MagicMock,
    ) -> None:
        mock_health.return_value = True
        mock_login.return_value = "admin-jwt"
        mock_bot_user.return_value = {"id": "uid", "name": "ingestion-bot"}
        mock_gen_token.return_value = "final-jwt-token"

        with patch("sys.argv", ["generate_bot_jwt.py"]):
            result = generate_bot_jwt.main()

        assert result == 0
        mock_health.assert_called_once()
        mock_login.assert_called_once()
        mock_bot_user.assert_called_once()
        mock_gen_token.assert_called_once()

    @patch("generate_bot_jwt.check_health")
    def test_om_unreachable(self, mock_health: MagicMock) -> None:
        mock_health.return_value = False

        with patch("sys.argv", ["generate_bot_jwt.py"]):
            result = generate_bot_jwt.main()

        assert result == 1

    @patch("generate_bot_jwt.login_admin")
    @patch("generate_bot_jwt.check_health")
    def test_login_failure(self, mock_health: MagicMock, mock_login: MagicMock) -> None:
        mock_health.return_value = True
        mock_login.return_value = None

        with patch("sys.argv", ["generate_bot_jwt.py"]):
            result = generate_bot_jwt.main()

        assert result == 1

    @patch("generate_bot_jwt.get_bot_user")
    @patch("generate_bot_jwt.login_admin")
    @patch("generate_bot_jwt.check_health")
    def test_bot_not_found(
        self,
        mock_health: MagicMock,
        mock_login: MagicMock,
        mock_bot_user: MagicMock,
    ) -> None:
        mock_health.return_value = True
        mock_login.return_value = "admin-jwt"
        mock_bot_user.return_value = None

        with patch("sys.argv", ["generate_bot_jwt.py"]):
            result = generate_bot_jwt.main()

        assert result == 1

    @patch("generate_bot_jwt.generate_token")
    @patch("generate_bot_jwt.get_bot_user")
    @patch("generate_bot_jwt.login_admin")
    @patch("generate_bot_jwt.check_health")
    def test_token_gen_failure(
        self,
        mock_health: MagicMock,
        mock_login: MagicMock,
        mock_bot_user: MagicMock,
        mock_gen_token: MagicMock,
    ) -> None:
        mock_health.return_value = True
        mock_login.return_value = "admin-jwt"
        mock_bot_user.return_value = {"id": "uid", "name": "ingestion-bot"}
        mock_gen_token.return_value = None

        with patch("sys.argv", ["generate_bot_jwt.py"]):
            result = generate_bot_jwt.main()

        assert result == 1
