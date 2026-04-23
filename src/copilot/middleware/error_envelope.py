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
"""Map typed exceptions and unhandled errors to the structured ErrorEnvelope.

Per .idea/Plan/Architecture/APIContract.md and .idea/Plan/Security/SecretsHandling.md
SC-8: error responses NEVER include API keys, JWTs, file paths, full prompts,
or raw exceptions. Only the canonical (code, message, request_id, ts) envelope.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from copilot.models import ErrorEnvelope
from copilot.models.chat import ErrorCode
from copilot.observability import get_logger

log = get_logger(__name__)

# Canonical mapping: error code -> safe human-readable message.
# Never use str(exception) - always use the canonical message.
SAFE_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.VALIDATION_FAILED: "Request body did not match the expected shape.",
    ErrorCode.TOOL_NOT_ALLOWLISTED: "The proposed tool is not in the allowlist.",
    ErrorCode.CONFIRMATION_REQUIRED: "User confirmation is required to proceed.",
    ErrorCode.CONFIRMATION_EXPIRED: "Confirmation window expired (5 min).",
    ErrorCode.PROPOSAL_NOT_FOUND: "Proposal id not found in this session.",
    ErrorCode.OM_UNAVAILABLE: "OpenMetadata is temporarily unreachable.",
    ErrorCode.OM_AUTH_FAILED: "OpenMetadata authentication failed.",
    ErrorCode.LLM_UNAVAILABLE: "AI is temporarily unreachable; try again in a minute.",
    ErrorCode.LLM_INVALID_OUTPUT: "AI returned an unexpected response.",
    ErrorCode.LLM_TOKEN_BUDGET_EXCEEDED: "Session token budget exceeded.",
    ErrorCode.GITHUB_UNAVAILABLE: "GitHub is temporarily unreachable.",
    ErrorCode.RATE_LIMITED: "Rate limit exceeded; try again in a minute.",
    ErrorCode.NOT_IMPLEMENTED: "This endpoint is scaffolded but not yet implemented.",
    ErrorCode.INTERNAL_ERROR: "Internal error. The team has been notified.",
}

STATUS_CODES: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.TOOL_NOT_ALLOWLISTED: 422,
    ErrorCode.CONFIRMATION_REQUIRED: 200,
    ErrorCode.CONFIRMATION_EXPIRED: 410,
    ErrorCode.PROPOSAL_NOT_FOUND: 422,
    ErrorCode.OM_UNAVAILABLE: 503,
    ErrorCode.OM_AUTH_FAILED: 502,
    ErrorCode.LLM_UNAVAILABLE: 503,
    ErrorCode.LLM_INVALID_OUTPUT: 502,
    ErrorCode.LLM_TOKEN_BUDGET_EXCEEDED: 429,
    ErrorCode.GITHUB_UNAVAILABLE: 503,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.NOT_IMPLEMENTED: 501,
    ErrorCode.INTERNAL_ERROR: 500,
}


class CopilotError(Exception):
    """Base class for typed errors that map to the envelope."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR


class McpUnavailable(CopilotError):
    code = ErrorCode.OM_UNAVAILABLE


class McpAuthFailed(CopilotError):
    code = ErrorCode.OM_AUTH_FAILED


class LlmUnavailable(CopilotError):
    code = ErrorCode.LLM_UNAVAILABLE


class LlmInvalidOutput(CopilotError):
    code = ErrorCode.LLM_INVALID_OUTPUT


class LlmTokenBudgetExceeded(CopilotError):
    code = ErrorCode.LLM_TOKEN_BUDGET_EXCEEDED


class ToolNotAllowlisted(CopilotError):
    code = ErrorCode.TOOL_NOT_ALLOWLISTED


class GithubUnavailable(CopilotError):
    code = ErrorCode.GITHUB_UNAVAILABLE


class ProposalNotFound(CopilotError):
    code = ErrorCode.PROPOSAL_NOT_FOUND


class ConfirmationExpired(CopilotError):
    code = ErrorCode.CONFIRMATION_EXPIRED


def _request_id_from(request: Request) -> UUID:
    """Best-effort: pull from RequestIdMiddleware state, else generate fresh."""
    rid = getattr(request.state, "request_id", None)
    return rid if isinstance(rid, UUID) else uuid4()


def _envelope(code: ErrorCode, request: Request) -> JSONResponse:
    payload = ErrorEnvelope(
        code=code,
        message=SAFE_MESSAGES[code],
        request_id=_request_id_from(request),
        ts=datetime.now(UTC),
    )
    return JSONResponse(
        status_code=STATUS_CODES[code],
        content=payload.model_dump(mode="json"),
    )


def register_envelope_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""

    @app.exception_handler(CopilotError)
    async def _handle_copilot_error(request: Request, exc: CopilotError) -> JSONResponse:
        log.warning("api.copilot_error", code=exc.code.value, exc_type=type(exc).__name__)
        return _envelope(exc.code, request)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        log.info("api.validation_failed", error_count=len(exc.errors()))
        return _envelope(ErrorCode.VALIDATION_FAILED, request)

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        log.error("api.unhandled_exception", exc_type=type(exc).__name__, exc_info=True)
        return _envelope(ErrorCode.INTERNAL_ERROR, request)
