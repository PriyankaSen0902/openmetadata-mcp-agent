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
"""Verify SC-1 (host=127.0.0.1) and SC-2 (SecretStr usage) from ThreatModel.md."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from copilot.config.settings import Settings, assert_runtime_env_ready

# Non-JWT-shaped value: scanners (e.g. GitGuardian) flag eyJ... three-segment tokens in PRs.
# Runtime checks only need a non-placeholder secret (see _is_placeholder_secret).
_UNIT_TEST_OM_SDK_TOKEN_OK = "copilot-unit-test-om-bot-credential-not-a-jwt-0123456789ab"


class TestSC1LoopbackBindOnly:
    """SC-1: FastAPI binds to 127.0.0.1 only in v1; 0.0.0.0 must NOT be the default."""

    def test_default_host_is_loopback(self) -> None:
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.host == "127.0.0.1", "SC-1: default host MUST be 127.0.0.1, never 0.0.0.0"


class TestSC2SecretStrTyping:
    """SC-2: secrets are SecretStr so accidental f-string interpolation cannot leak."""

    def test_ai_sdk_token_is_secret_str(self) -> None:
        s = Settings(_env_file=None, ai_sdk_token="totally-real-jwt-do-not-leak")  # type: ignore[call-arg]
        assert isinstance(s.ai_sdk_token, SecretStr)
        assert "do-not-leak" not in str(s.ai_sdk_token)
        assert "do-not-leak" not in repr(s.ai_sdk_token)

    def test_openai_api_key_is_secret_str(self) -> None:
        s = Settings(_env_file=None, openai_api_key="sk-totally-real-key-do-not-leak")  # type: ignore[call-arg]
        assert isinstance(s.openai_api_key, SecretStr)
        assert "do-not-leak" not in str(s.openai_api_key)
        assert "do-not-leak" not in repr(s.openai_api_key)

    def test_secret_value_extractable_with_explicit_call(self) -> None:
        s = Settings(_env_file=None, ai_sdk_token="real-value-here")  # type: ignore[call-arg]
        assert s.ai_sdk_token.get_secret_value() == "real-value-here"


class TestResilienceKnobs:
    """NFRs.md timeouts / retries default to safe values."""

    def test_om_timeout_default(self) -> None:
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.om_timeout_seconds == pytest.approx(5.0)

    def test_om_mcp_http_path_default(self) -> None:
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.om_mcp_http_path == "/mcp"

    def test_om_mcp_http_path_strips_and_prefixes_slash(self) -> None:
        s = Settings(_env_file=None, om_mcp_http_path="api/v1/mcp")  # type: ignore[call-arg]
        assert s.om_mcp_http_path == "/api/v1/mcp"

    def test_openai_timeout_default(self) -> None:
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.openai_timeout_seconds == pytest.approx(8.0)
        assert s.openai_max_retries == 2


class TestRuntimeEnvValidation:
    """Startup guard: reject .env.example placeholders when not under pytest."""

    def test_github_token_empty_string_becomes_none(self) -> None:
        s = Settings(_env_file=None, github_token="")  # type: ignore[call-arg]
        assert s.github_token is None

    def test_assert_runtime_rejects_om_placeholder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PYTEST_VERSION", raising=False)
        monkeypatch.delenv("COPILOT_SKIP_ENV_VALIDATION", raising=False)
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            ai_sdk_host="http://localhost:8585",
            ai_sdk_token="paste-your-bot-jwt-here",
            openai_api_key="sk-abcdefghijklmnopqrstuvwxyz0123456789",
        )
        with pytest.raises(RuntimeError, match="AI_SDK_TOKEN"):
            assert_runtime_env_ready(s)

    def test_assert_runtime_rejects_openai_placeholder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTEST_VERSION", raising=False)
        monkeypatch.delenv("COPILOT_SKIP_ENV_VALIDATION", raising=False)
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            ai_sdk_host="http://localhost:8585",
            ai_sdk_token=_UNIT_TEST_OM_SDK_TOKEN_OK,
            openai_api_key="sk-paste-your-key-here",
        )
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            assert_runtime_env_ready(s)

    def test_assert_runtime_skipped_under_pytest(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PYTEST_VERSION", "8.0.0")
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            ai_sdk_host="http://localhost:8585",
            ai_sdk_token="paste-your-bot-jwt-here",
            openai_api_key="sk-paste-your-key-here",
        )
        assert_runtime_env_ready(s)  # does not raise

    def test_github_template_pat_becomes_none(self) -> None:
        s = Settings(_env_file=None, github_token="ghp_your_fine_grained_pat_here")  # type: ignore[call-arg]
        assert s.github_token is None

    def test_assert_runtime_ok_when_github_was_template_pat(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTEST_VERSION", raising=False)
        monkeypatch.delenv("COPILOT_SKIP_ENV_VALIDATION", raising=False)
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            ai_sdk_host="http://localhost:8585",
            ai_sdk_token=_UNIT_TEST_OM_SDK_TOKEN_OK,
            openai_api_key="sk-abcdefghijklmnopqrstuvwxyz0123456789",
            github_token="ghp_your_fine_grained_pat_here",
        )
        assert_runtime_env_ready(s)

    def test_assert_runtime_accepts_utf8_bom_and_wrapping_quotes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Windows editors sometimes save UTF-8 BOM; users sometimes wrap values in quotes."""
        monkeypatch.delenv("PYTEST_VERSION", raising=False)
        monkeypatch.delenv("COPILOT_SKIP_ENV_VALIDATION", raising=False)
        wrapped = f"'{_UNIT_TEST_OM_SDK_TOKEN_OK}'"
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            ai_sdk_host="http://localhost:8585",
            ai_sdk_token=wrapped,
            openai_api_key="\ufeffsk-abcdefghijklmnopqrstuvwxyz0123456789",
        )
        assert_runtime_env_ready(s)
