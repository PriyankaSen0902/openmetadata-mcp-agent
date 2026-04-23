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
"""Chat routes for the public API surface.

Per .idea/Plan/Architecture/APIContract.md:
  POST /api/v1/chat            user submits NL message
  POST /api/v1/chat/confirm    user accepts/rejects pending write proposal
  POST /api/v1/chat/cancel     user clears the session

POST /api/v1/chat is functional in Phase 2; confirm/cancel use the in-memory
session store (P2-19).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from copilot.services.agent import run_chat_turn
from copilot.services.sessions import cancel_chat_session, confirm_chat_proposal

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """POST /api/v1/chat request shape."""

    message: str = Field(min_length=1, max_length=4000)
    session_id: UUID | None = None


class ChatConfirmRequest(BaseModel):
    """POST /api/v1/chat/confirm request shape."""

    session_id: UUID
    proposal_id: UUID
    accepted: bool


class ChatCancelRequest(BaseModel):
    """POST /api/v1/chat/cancel request shape."""

    session_id: UUID


@router.post("/chat", summary="Submit a chat message")
async def post_chat(request: Request, body: ChatRequest) -> JSONResponse:
    """Execute a chat turn through the agent pipeline."""
    request_id = getattr(request.state, "request_id", None)
    result = await run_chat_turn(
        user_message=body.message,
        session_id=str(body.session_id) if body.session_id else None,
        request_id=request_id,
    )
    return JSONResponse(status_code=200, content=result)


@router.post("/chat/confirm", summary="Confirm a pending write proposal")
async def post_chat_confirm(request: Request, body: ChatConfirmRequest) -> JSONResponse:
    """Execute or reject a pending write via ``services.sessions``."""
    rid = getattr(request.state, "request_id", None)
    request_uuid = rid if isinstance(rid, UUID) else uuid4()
    result = await confirm_chat_proposal(
        body.session_id,
        body.proposal_id,
        body.accepted,
        request_id=request_uuid,
    )
    return JSONResponse(status_code=200, content=result)


@router.post("/chat/cancel", summary="Cancel the current chat session")
async def post_chat_cancel(_request: Request, body: ChatCancelRequest) -> JSONResponse:
    """Clear pending HITL state for the session."""
    result = await cancel_chat_session(body.session_id)
    return JSONResponse(status_code=200, content=result)
