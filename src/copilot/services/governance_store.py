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
"""In-memory per-FQN governance FSM store (P2-20).

Callers must use a canonical entity FQN string as the key; the store does not
normalize aliases. LangGraph / confirm-path integration is P2-21 (#77).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from copilot.models.governance_record import EntityGovernanceRecord
from copilot.models.governance_state import GovernanceState, allowed_targets
from copilot.observability import get_logger

log = get_logger(__name__)

_lock = asyncio.Lock()
_by_fqn: dict[str, EntityGovernanceRecord] = {}


class GovernanceTransitionError(Exception):
    """Raised when ``transition`` requests a disallowed FSM edge."""

    def __init__(
        self,
        *,
        fqn: str,
        from_state: GovernanceState,
        to_state: GovernanceState,
    ) -> None:
        self.fqn = fqn
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Illegal governance transition for {fqn!r}: {from_state.value} -> {to_state.value}",
        )


def _truncate_evidence(text: str | None, max_len: int = 500) -> str | None:
    if text is None:
        return None
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


async def reset_governance_store_for_tests() -> None:
    """Clear all rows (pytest only)."""
    async with _lock:
        _by_fqn.clear()


async def get_or_create(fqn: str) -> EntityGovernanceRecord:
    """Return the governance row for ``fqn``, creating UNKNOWN if missing."""
    async with _lock:
        row = _by_fqn.get(fqn)
        if row is None:
            row = EntityGovernanceRecord(fqn=fqn)
            _by_fqn[fqn] = row
        return row


async def get_approved_fqns() -> list[str]:
    """Return a list of FQNs that are in APPROVED or ENFORCED states."""
    async with _lock:
        return [
            fqn for fqn, row in _by_fqn.items()
            if row.state in (GovernanceState.APPROVED, GovernanceState.ENFORCED)
        ]


async def transition(
    fqn: str,
    to: GovernanceState,
    *,
    evidence: str | None = None,
) -> EntityGovernanceRecord:
    """Apply one allowed FSM transition; raises ``GovernanceTransitionError`` if illegal."""
    async with _lock:
        row = _by_fqn.get(fqn)
        if row is None:
            row = EntityGovernanceRecord(fqn=fqn)
            _by_fqn[fqn] = row

        current = row.state
        if to not in allowed_targets(current):
            log.warning(
                "governance_store.transition.denied",
                fqn=fqn,
                from_state=current.value,
                to_state=to.value,
            )
            raise GovernanceTransitionError(fqn=fqn, from_state=current, to_state=to)

        now = datetime.now(UTC)
        updated = row.model_copy(
            update={
                "state": to,
                "updated_at": now,
                "last_evidence": _truncate_evidence(evidence),
            },
        )
        _by_fqn[fqn] = updated
        log.info(
            "governance_store.transition.ok",
            fqn=fqn,
            from_state=current.value,
            to_state=to.value,
        )
        return updated
