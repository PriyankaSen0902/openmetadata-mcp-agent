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
"""Unit tests for Phase 3 mock GitHub MCP client."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from copilot.clients.github_mcp import call_tool
from copilot.config import get_settings
from copilot.middleware.error_envelope import McpAuthFailed, McpUnavailable


def test_call_tool_auth_failure() -> None:
    """Test auth failure when github_token is missing."""
    settings = get_settings()
    old_token = settings.github_token
    settings.github_token = None

    with pytest.raises(McpAuthFailed, match="GITHUB_TOKEN is not set"):
        call_tool("github_create_issue", {})

    settings.github_token = old_token


def test_call_tool_unsupported() -> None:
    """Test unsupported tool."""
    settings = get_settings()
    settings.github_token = SecretStr("mock-token")

    with pytest.raises(McpUnavailable, match="not supported"):
        call_tool("unsupported_tool", {})


def test_call_tool_success() -> None:
    """Test mock issue creation."""
    settings = get_settings()
    settings.github_token = SecretStr("mock-token")

    result = call_tool(
        "github_create_issue", {"repo": "my/repo", "title": "Test Title", "body": "Test Body"}
    )

    assert result["title"] == "Test Title"
    assert result["status"] == "created"
    assert "https://github.com/my/repo/issues/" in result["issue_url"]
