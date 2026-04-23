#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Smoke tests: every module imports cleanly + the app boots + /healthz returns 200."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestModuleImports:
    """Imports every module to catch syntax or circular-import problems."""

    def test_imports_succeed(self) -> None:
        import copilot
        from copilot.api import chat, main
        from copilot.clients import om_mcp, openai_client
        from copilot.config import settings
        from copilot.middleware import error_envelope, rate_limit, request_id
        from copilot.models import chat as chat_models
        from copilot.observability import metrics, redact
        from copilot.services import agent, prompt_safety

        assert copilot.__version__
        assert main.create_app
        assert chat.router is not None
        assert om_mcp.call_tool
        assert openai_client.call_chat
        assert settings.Settings
        assert error_envelope.register_envelope_handlers
        assert rate_limit.build_limiter
        assert request_id.RequestIdMiddleware
        assert chat_models.ChatSession
        assert metrics.REGISTRY is not None
        assert redact.make_redaction_processor
        assert agent.assert_tool_allowlisted
        assert prompt_safety.neutralize


class TestHealthz:
    def test_healthz_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/healthz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "version" in body
        assert "ts" in body
        assert body["checks"]["app"]["ok"] is True

    def test_healthz_includes_request_id_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/healthz")
        assert "x-request-id" in {k.lower() for k in response.headers}


class TestMetricsEndpoint:
    def test_metrics_returns_prometheus_text(self, client: TestClient) -> None:
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestChatRoute:
    @patch("copilot.api.chat.run_chat_turn", new_callable=AsyncMock)
    def test_chat_forwards_request_id_to_agent(
        self, mock_run_chat_turn: AsyncMock, client: TestClient
    ) -> None:
        request_id = "fddf6e8c-a479-4b9c-8b74-5dfcc0e57035"
        mock_run_chat_turn.return_value = {
            "request_id": request_id,
            "session_id": "ef11cf79-d79f-435c-9630-dd405dbbe21d",
            "response": "Found matching tables.",
            "response_format": "markdown",
            "audit_log": [{"tool_name": "semantic_search", "duration_ms": 12, "success": True}],
            "tokens_used": {"prompt": 10, "completion": 5},
            "ts": "2026-04-22T15:00:00+00:00",
        }

        response = client.post(
            "/api/v1/chat",
            headers={"X-Request-Id": request_id},
            json={"message": "show me some tables"},
        )

        assert response.status_code == 200
        body = response.json()
        assert response.headers["X-Request-Id"] == request_id
        assert body["request_id"] == request_id
        assert body["response"] == "Found matching tables."

        mock_run_chat_turn.assert_awaited_once()
        kwargs = mock_run_chat_turn.await_args.kwargs
        assert kwargs["user_message"] == "show me some tables"
        assert kwargs["session_id"] is None
        assert str(kwargs["request_id"]) == request_id

    @patch("copilot.api.chat.run_chat_turn", new_callable=AsyncMock)
    def test_chat_returns_safe_error_envelope_on_unhandled_error(
        self, mock_run_chat_turn: AsyncMock, client: TestClient
    ) -> None:
        mock_run_chat_turn.side_effect = RuntimeError("token=secret-value")

        response = client.post("/api/v1/chat", json={"message": "trigger error"})

        assert response.status_code == 500
        body = response.json()
        assert body["code"] == "internal_error"
        assert "request_id" in body
        assert "ts" in body
        assert "secret-value" not in body["message"]
