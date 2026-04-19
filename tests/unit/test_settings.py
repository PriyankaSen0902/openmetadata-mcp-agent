#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Verify SC-1 (host=127.0.0.1) and SC-2 (SecretStr usage) from ThreatModel.md."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from copilot.config.settings import Settings


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
        assert s.om_max_retries == 3

    def test_openai_timeout_default(self) -> None:
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.openai_timeout_seconds == pytest.approx(8.0)
        assert s.openai_max_retries == 2
