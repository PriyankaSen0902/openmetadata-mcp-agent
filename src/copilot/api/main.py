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
"""FastAPI app factory + /healthz + /metrics + /chat + /governance/drift.

Per .idea/Plan/Architecture/APIContract.md:
  - GET  /api/v1/healthz            functional in Phase 1 (boots without dependencies)
  - GET  /api/v1/metrics            functional in Phase 1 (Prometheus text format)
  - POST /api/v1/chat               functional in Phase 2 via the LangGraph agent
  - POST /api/v1/chat/confirm       P2-19 session store + OM MCP execute on accept
  - POST /api/v1/chat/cancel        clears pending session state (P2-19)
  - GET  /api/v1/governance/drift   functional in Phase 2 (drift detection)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from copilot import __version__
from copilot.api import chat as chat_routes
from copilot.api import governance as governance_routes
from copilot.config import assert_runtime_env_ready, get_settings
from copilot.middleware import (
    RequestIdMiddleware,
    build_limiter,
    register_envelope_handlers,
)
from copilot.middleware.rate_limit import attach_limiter
from copilot.observability import configure_observability, get_logger
from copilot.observability.metrics import render_prometheus_text


async def _drift_poll_loop(interval: float) -> None:
    """Background task: run drift scans at a fixed interval.

    Catches all exceptions so the loop never crashes the process (NFR-03).
    """
    from copilot.services.drift import run_drift_scan

    log = get_logger(__name__)
    log.info("drift.poll_loop.start", interval_s=interval)

    while True:
        try:
            await run_drift_scan()
        except Exception:
            log.exception("drift.poll_loop.unhandled")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Lifespan: configure observability + start drift poll at startup."""
    configure_observability()
    log = get_logger(__name__)
    settings = get_settings()
    assert_runtime_env_ready(settings)
    log.info(
        "app.startup",
        version=__version__,
        host=settings.host,
        port=settings.port,
        om_host=settings.ai_sdk_host,
        model=settings.openai_model,
    )

    # Start the background drift poll task
    drift_task = asyncio.create_task(
        _drift_poll_loop(settings.drift_poll_interval_seconds),
    )

    yield

    drift_task.cancel()
    with suppress(asyncio.CancelledError):
        await drift_task
    log.info("app.shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI app."""
    app = FastAPI(
        title="openmetadata-mcp-agent",
        version=__version__,
        description="Conversational governance agent for OpenMetadata.",
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-Id"],
    )
    attach_limiter(app, build_limiter())
    register_envelope_handlers(app)

    @app.get("/api/v1/healthz", tags=["system"])
    async def healthz(_request: Request) -> dict[str, Any]:
        """Liveness probe. Returns 200 if the process is up."""
        # Phase 1: no upstream checks yet; OM/OpenAI checks land in P2.
        return {
            "status": "ok",
            "version": __version__,
            "ts": datetime.now(UTC).isoformat(),
            "checks": {"app": {"ok": True}},
        }

    @app.get("/api/v1/metrics", tags=["system"])
    async def metrics() -> Response:
        """Prometheus text-format metrics. 4 Golden Signals + token usage + breaker state."""
        payload, content_type = render_prometheus_text()
        return Response(content=payload, media_type=content_type)

    app.include_router(chat_routes.router, prefix="/api/v1")
    app.include_router(governance_routes.router, prefix="/api/v1")
    return app


# Module-level app for `uvicorn copilot.api.main:app`
app = create_app()


def run() -> None:
    """Entry point for `python -m copilot` / `copilot` console script."""
    settings = get_settings()
    uvicorn.run(
        "copilot.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
