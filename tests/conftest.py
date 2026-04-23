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
"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# Set safe defaults BEFORE the app imports so Settings doesn't fail validation.
os.environ.setdefault("AI_SDK_TOKEN", "test-token-placeholder-not-real-jwt")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder-not-real-key")
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "warning")  # quieter test output


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A FastAPI TestClient for HTTP-level tests.

    Imports inside the fixture so pytest collection doesn't fail when an env
    var is missing in CI.
    """
    from copilot.api.main import create_app

    app = create_app()
    # Starlette BaseHTTPMiddleware can wrap route exceptions in ExceptionGroup;
    # raise_server_exceptions=True surfaces that to pytest instead of the HTTP
    # response from register_envelope_handlers (breaks error-envelope asserts on
    # Python 3.13+). False keeps tests aligned with real clients.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
