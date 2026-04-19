#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Smoke tests: every module imports cleanly + the app boots + /healthz returns 200."""

from __future__ import annotations

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


class TestChatStub:
    def test_chat_returns_not_implemented_envelope(self, client: TestClient) -> None:
        response = client.post("/api/v1/chat", json={"message": "hello"})
        assert response.status_code == 501
        body = response.json()
        assert body["code"] == "not_implemented"
        assert "request_id" in body
        assert "ts" in body
        assert "secret" not in body["message"].lower()  # SC-8: no secrets in errors
