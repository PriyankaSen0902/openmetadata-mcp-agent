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
"""In-memory proposal store for HITL confirmation flow.

Minimal implementation for P2-12 (issue #84).  Stores pending
``ToolCallProposal`` objects keyed by ``proposal_id``.  Single-process,
no persistence — sufficient for the hackathon demo.

A durable, multi-process session store is tracked in issue #75.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from copilot.models.chat import ToolCallProposal
from copilot.observability import get_logger

log = get_logger(__name__)

# proposal_id (str) → ToolCallProposal
_pending: dict[str, ToolCallProposal] = {}


def store_proposal(proposal: ToolCallProposal) -> None:
    """Persist a proposal for later confirmation."""
    key = str(proposal.proposal_id)
    _pending[key] = proposal
    log.info("session_store.store", proposal_id=key, tool=str(proposal.tool_name))


def get_proposal(proposal_id: UUID | str) -> ToolCallProposal | None:
    """Look up a pending proposal.  Returns ``None`` if not found."""
    return _pending.get(str(proposal_id))


def remove_proposal(proposal_id: UUID | str) -> ToolCallProposal | None:
    """Remove and return a proposal (consume-once semantics)."""
    return _pending.pop(str(proposal_id), None)


def is_expired(proposal: ToolCallProposal) -> bool:
    """Check whether a proposal's TTL has elapsed."""
    if proposal.expires_at is None:
        return False
    return datetime.now(UTC) >= proposal.expires_at


def clear_all() -> None:
    """Clear every stored proposal.  Useful in tests."""
    _pending.clear()
