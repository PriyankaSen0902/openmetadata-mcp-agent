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
"""Unit tests for HITL session store + confirm/cancel services."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from copilot.middleware.error_envelope import ConfirmationExpired, ProposalNotFound
from copilot.models import RiskLevel, ToolCallProposal, ToolName
from copilot.services.sessions import (
    cancel_chat_session,
    confirm_chat_proposal,
    reset_session_store_for_tests,
    set_pending,
)


@pytest.fixture(autouse=True)
async def _clean_session_store() -> None:
    await reset_session_store_for_tests()
    yield
    await reset_session_store_for_tests()


def _write_proposal(
    *,
    session_request_id: UUID | None = None,
    proposal_id: UUID | None = None,
    expires_delta: timedelta | None = None,
) -> ToolCallProposal:
    rid = session_request_id or uuid4()
    pid = proposal_id if proposal_id is not None else uuid4()
    exp = datetime.now(UTC) + (expires_delta if expires_delta is not None else timedelta(minutes=5))
    return ToolCallProposal(
        proposal_id=pid,
        request_id=rid,
        tool_name=ToolName.PATCH_ENTITY,
        arguments={"entityType": "table", "entityFqn": "db.schema.t", "patch": []},
        risk_level=RiskLevel.HARD_WRITE,
        expires_at=exp,
    )


@pytest.mark.asyncio
async def test_confirm_accept_happy_path_calls_mcp_and_clears_store() -> None:
    sid = uuid4()
    req = uuid4()
    prop = _write_proposal(session_request_id=req)
    pid = prop.proposal_id
    await set_pending(sid, prop)

    with patch("copilot.services.sessions.om_mcp.call_tool", return_value={"ok": True}) as m:
        out = await confirm_chat_proposal(sid, pid, True, request_id=uuid4())

    m.assert_called_once_with("patch_entity", prop.arguments)
    assert out["session_id"] == str(sid)
    assert len(out["audit_log"]) == 1
    assert out["audit_log"][0]["confirmed_by_user"] is True
    assert out["audit_log"][0]["success"] is True

    with pytest.raises(ProposalNotFound):
        await confirm_chat_proposal(sid, pid, True, request_id=uuid4())


@pytest.mark.asyncio
async def test_confirm_expired_raises_and_clears() -> None:
    sid = uuid4()
    prop = _write_proposal(expires_delta=timedelta(seconds=-30))
    await set_pending(sid, prop)

    with pytest.raises(ConfirmationExpired):
        await confirm_chat_proposal(sid, prop.proposal_id, True, request_id=uuid4())

    with pytest.raises(ProposalNotFound):
        await confirm_chat_proposal(sid, prop.proposal_id, True, request_id=uuid4())


@pytest.mark.asyncio
async def test_confirm_proposal_not_found_wrong_id() -> None:
    sid = uuid4()
    prop = _write_proposal()
    await set_pending(sid, prop)

    with pytest.raises(ProposalNotFound):
        await confirm_chat_proposal(sid, uuid4(), True, request_id=uuid4())


@pytest.mark.asyncio
async def test_confirm_reject_does_not_call_mcp() -> None:
    sid = uuid4()
    prop = _write_proposal()
    await set_pending(sid, prop)

    with patch("copilot.services.sessions.om_mcp.call_tool") as m:
        out = await confirm_chat_proposal(sid, prop.proposal_id, False, request_id=uuid4())

    m.assert_not_called()
    assert out["audit_log"] == []
    assert "Cancelled" in out["response"]

    with pytest.raises(ProposalNotFound):
        await confirm_chat_proposal(sid, prop.proposal_id, True, request_id=uuid4())


@pytest.mark.asyncio
async def test_cancel_clears_pending() -> None:
    sid = uuid4()
    prop = _write_proposal()
    await set_pending(sid, prop)

    out = await cancel_chat_session(sid)
    assert out["cancelled"] is True
    assert out["session_id"] == str(sid)

    with pytest.raises(ProposalNotFound):
        await confirm_chat_proposal(sid, prop.proposal_id, True, request_id=uuid4())


@pytest.mark.asyncio
async def test_post_chat_confirm_http_200(client: TestClient) -> None:
    """POST /chat/confirm returns 200 when store + MCP are satisfied."""
    await reset_session_store_for_tests()
    sid = uuid4()
    prop = _write_proposal()
    await set_pending(sid, prop)

    with patch("copilot.services.sessions.om_mcp.call_tool", return_value={"ok": True}):
        r = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(prop.proposal_id),
                "accepted": True,
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == str(sid)
    assert body["audit_log"][0]["tool_name"] == "patch_entity"
