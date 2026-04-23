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
"""In-memory pending HITL proposals keyed by session_id (P2-19)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from copilot.clients import om_mcp
from copilot.middleware.error_envelope import ConfirmationExpired, ProposalNotFound
from copilot.models.chat import PendingSession, ToolCallProposal
from copilot.observability import get_logger
from copilot.services.tool_audit import summarize_tool_result

log = get_logger(__name__)

_lock = asyncio.Lock()
_by_session: dict[str, PendingSession] = {}


async def reset_session_store_for_tests() -> None:
    """Clear all session rows (pytest only)."""
    async with _lock:
        _by_session.clear()


async def set_pending(session_id: UUID, proposal: ToolCallProposal) -> None:
    """Record a write proposal awaiting POST /chat/confirm."""
    now = datetime.now(UTC)
    key = str(session_id)
    async with _lock:
        _by_session[key] = PendingSession(
            session_id=session_id,
            pending=proposal,
            expires_at=proposal.expires_at,
            updated_at=now,
        )
    log.info(
        "sessions.set_pending",
        session_id=key,
        proposal_id=str(proposal.proposal_id),
        tool=str(proposal.tool_name),
    )


async def clear_session(session_id: UUID) -> None:
    """Remove pending state for a session (cancel or after confirm)."""
    key = str(session_id)
    async with _lock:
        _by_session.pop(key, None)
    log.info("sessions.clear_session", session_id=key)


async def cancel_chat_session(session_id: UUID) -> dict[str, Any]:
    """Clear pending proposal for session; idempotent."""
    await clear_session(session_id)
    return {
        "session_id": str(session_id),
        "cancelled": True,
        "ts": datetime.now(UTC).isoformat(),
    }


def _is_expired(proposal: ToolCallProposal, now: datetime) -> bool:
    exp = proposal.expires_at
    return exp is not None and now > exp


async def confirm_chat_proposal(
    session_id: UUID,
    proposal_id: UUID,
    accepted: bool,
    *,
    request_id: UUID,
) -> dict[str, Any]:
    """Validate pending proposal, optionally execute write via OM MCP, return APIContract 200 body."""
    now = datetime.now(UTC)
    key = str(session_id)

    async with _lock:
        row = _by_session.get(key)
        pending = row.pending if row else None
        if pending is None or pending.proposal_id != proposal_id:
            log.warning(
                "sessions.confirm.proposal_not_found",
                session_id=key,
                proposal_id=str(proposal_id),
            )
            raise ProposalNotFound()
        if _is_expired(pending, now):
            _by_session.pop(key, None)
            log.warning(
                "sessions.confirm.expired",
                session_id=key,
                proposal_id=str(proposal_id),
            )
            raise ConfirmationExpired()
        _by_session.pop(key, None)

    if not accepted:
        log.info(
            "sessions.confirm.rejected",
            session_id=key,
            proposal_id=str(proposal_id),
        )
        return {
            "request_id": str(request_id),
            "session_id": key,
            "response": "Cancelled. No changes were made. Anything else?",
            "audit_log": [],
            "ts": now.isoformat(),
        }

    start = datetime.now(UTC)
    tool_name = str(pending.tool_name)
    result = await asyncio.to_thread(om_mcp.call_tool, tool_name, pending.arguments)
    end = datetime.now(UTC)
    duration_ms = int((end - start).total_seconds() * 1000)
    log.info(
        "sessions.confirm.executed",
        session_id=key,
        proposal_id=str(proposal_id),
        tool=tool_name,
        duration_ms=duration_ms,
    )

    return {
        "request_id": str(request_id),
        "session_id": key,
        "response": _success_message(tool_name, summarize_tool_result(result)),
        "audit_log": [
            {
                "tool_name": tool_name,
                "confirmed_by_user": True,
                "duration_ms": duration_ms,
                "success": True,
            }
        ],
        "ts": end.isoformat(),
    }


def _success_message(tool_name: str, summary: str) -> str:
    base = f"Done. Executed `{tool_name}`."
    if summary:
        return f"{base} {summary[:400]}"
    return base
