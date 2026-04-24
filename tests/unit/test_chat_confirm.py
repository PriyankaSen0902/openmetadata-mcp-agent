#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Tests for POST /api/v1/chat/confirm (HITL) + ``session_store`` helpers.

Covers:
  - Confirm with valid session + proposal_id → 200, write-back path invoked
  - Reject → 200, no write-back
  - Unknown proposal / session mismatch → 422 proposal_not_found
  - Expired proposal → 410 confirmation_expired
  - Double-confirm → first 200, second 422
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from copilot.models import RiskLevel, ToolCallProposal, ToolName
from copilot.services import session_store
from copilot.services.governance_store import reset_governance_store_for_tests
from copilot.services.sessions import reset_session_store_for_tests, set_pending


@pytest.fixture(autouse=True)
async def _clean_stores() -> AsyncGenerator[None, None]:
    """Ensure clean session + governance + proposal-id store for every test."""
    await reset_session_store_for_tests()
    session_store.clear_all()
    await reset_governance_store_for_tests()
    yield
    await reset_session_store_for_tests()
    session_store.clear_all()
    await reset_governance_store_for_tests()


def _make_proposal(
    *,
    tool: ToolName = ToolName.PATCH_ENTITY,
    risk: RiskLevel = RiskLevel.HARD_WRITE,
    expired: bool = False,
    proposal_id: UUID | None = None,
) -> ToolCallProposal:
    """Build a ToolCallProposal aligned with governance confirm paths."""
    now = datetime.now(UTC)
    exp = now - timedelta(minutes=1) if expired else now + timedelta(minutes=5)
    return ToolCallProposal(
        proposal_id=proposal_id if proposal_id is not None else uuid4(),
        request_id=uuid4(),
        tool_name=tool,
        arguments={"entityType": "table", "entityFqn": "db.schema.t", "patch": []},
        risk_level=risk,
        rationale="Apply change",
        expires_at=exp,
    )


class TestConfirmAccepted:
    """Confirm with accepted=true → write-back enqueued, 200."""

    @pytest.mark.asyncio
    async def test_confirm_enqueues_writeback(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal()
        await set_pending(sid, proposal)

        with patch(
            "copilot.services.sessions.enqueue_writeback_for_state",
            new_callable=AsyncMock,
        ):
            response = client.post(
                "/api/v1/chat/confirm",
                json={
                    "session_id": str(sid),
                    "proposal_id": str(proposal.proposal_id),
                    "accepted": True,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"] == str(sid)
        assert "Done." in body["response"]
        assert body["audit_log"][0]["confirmed_by_user"] is True
        assert body["audit_log"][0]["success"] is True
        assert body["audit_log"][0]["tool_name"] == "patch_entity"

    @pytest.mark.asyncio
    async def test_confirm_consumes_proposal(self, client: TestClient) -> None:
        """After confirmation, the same session cannot confirm again."""
        sid = uuid4()
        proposal = _make_proposal()
        await set_pending(sid, proposal)

        with patch(
            "copilot.services.sessions.enqueue_writeback_for_state",
            new_callable=AsyncMock,
        ):
            first = client.post(
                "/api/v1/chat/confirm",
                json={
                    "session_id": str(sid),
                    "proposal_id": str(proposal.proposal_id),
                    "accepted": True,
                },
            )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(proposal.proposal_id),
                "accepted": True,
            },
        )
        assert second.status_code == 422
        assert second.json()["code"] == "proposal_not_found"


class TestConfirmRejected:
    """Confirm with accepted=false → 200, no write-back."""

    @pytest.mark.asyncio
    async def test_reject_returns_cancellation(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal()
        await set_pending(sid, proposal)

        with patch(
            "copilot.services.sessions.enqueue_writeback_for_state",
            new_callable=AsyncMock,
        ) as m:
            response = client.post(
                "/api/v1/chat/confirm",
                json={
                    "session_id": str(sid),
                    "proposal_id": str(proposal.proposal_id),
                    "accepted": False,
                },
            )

        m.assert_not_awaited()
        assert response.status_code == 200
        body = response.json()
        assert "Cancelled" in body["response"]
        assert body["audit_log"] == []

    @pytest.mark.asyncio
    async def test_reject_clears_pending(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal()
        await set_pending(sid, proposal)

        client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(proposal.proposal_id),
                "accepted": False,
            },
        )

        retry = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(proposal.proposal_id),
                "accepted": True,
            },
        )
        assert retry.status_code == 422
        assert retry.json()["code"] == "proposal_not_found"


class TestConfirmNotFound:
    """Unknown proposal_id for session → 422 proposal_not_found."""

    def test_unknown_proposal_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(uuid4()),
                "proposal_id": str(uuid4()),
                "accepted": True,
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "proposal_not_found"

    @pytest.mark.asyncio
    async def test_wrong_proposal_id_for_session_returns_422(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal()
        await set_pending(sid, proposal)

        response = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(uuid4()),
                "accepted": True,
            },
        )
        assert response.status_code == 422
        assert response.json()["code"] == "proposal_not_found"


class TestConfirmExpired:
    """Expired proposal → 410 confirmation_expired."""

    @pytest.mark.asyncio
    async def test_expired_proposal_returns_410(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal(expired=True)
        await set_pending(sid, proposal)

        response = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(proposal.proposal_id),
                "accepted": True,
            },
        )

        assert response.status_code == 410
        body = response.json()
        assert body["code"] == "confirmation_expired"

    @pytest.mark.asyncio
    async def test_expired_proposal_clears_row(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal(expired=True)
        await set_pending(sid, proposal)

        client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(proposal.proposal_id),
                "accepted": True,
            },
        )

        retry = client.post(
            "/api/v1/chat/confirm",
            json={
                "session_id": str(sid),
                "proposal_id": str(proposal.proposal_id),
                "accepted": True,
            },
        )
        assert retry.status_code == 422


class TestDoubleConfirm:
    """Double-confirm: first wins, second gets proposal_not_found."""

    @pytest.mark.asyncio
    async def test_second_confirm_returns_not_found(self, client: TestClient) -> None:
        sid = uuid4()
        proposal = _make_proposal()
        await set_pending(sid, proposal)
        body = {
            "session_id": str(sid),
            "proposal_id": str(proposal.proposal_id),
            "accepted": True,
        }

        with patch(
            "copilot.services.sessions.enqueue_writeback_for_state",
            new_callable=AsyncMock,
        ):
            first = client.post("/api/v1/chat/confirm", json=body)
        assert first.status_code == 200

        second = client.post("/api/v1/chat/confirm", json=body)
        assert second.status_code == 422
        assert second.json()["code"] == "proposal_not_found"


class TestSessionStore:
    """Unit tests for the ``session_store`` module (proposal_id keyed cache)."""

    def test_store_and_get(self) -> None:
        proposal = _make_proposal()
        session_store.store_proposal(proposal)
        assert session_store.get_proposal(proposal.proposal_id) is proposal

    def test_remove(self) -> None:
        proposal = _make_proposal()
        session_store.store_proposal(proposal)
        removed = session_store.remove_proposal(proposal.proposal_id)
        assert removed is proposal
        assert session_store.get_proposal(proposal.proposal_id) is None

    def test_remove_missing_returns_none(self) -> None:
        assert session_store.remove_proposal(uuid4()) is None

    def test_is_expired_false(self) -> None:
        proposal = _make_proposal(expired=False)
        assert not session_store.is_expired(proposal)

    def test_is_expired_true(self) -> None:
        proposal = _make_proposal(expired=True)
        assert session_store.is_expired(proposal)

    def test_is_expired_no_ttl(self) -> None:
        proposal = ToolCallProposal(
            request_id=uuid4(),
            tool_name=ToolName.PATCH_ENTITY,
            arguments={},
            risk_level=RiskLevel.HARD_WRITE,
            expires_at=None,
        )
        assert not session_store.is_expired(proposal)

    def test_clear_all(self) -> None:
        pid = uuid4()
        proposal = _make_proposal(proposal_id=pid)
        session_store.store_proposal(proposal)
        session_store.clear_all()
        assert session_store.get_proposal(pid) is None
