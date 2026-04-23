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
"""Unit tests for governance FSM + in-memory store (P2-20)."""

from __future__ import annotations

from collections import deque

import pytest

from copilot.models.governance_state import ALLOWED_TRANSITIONS, GovernanceState, allowed_targets
from copilot.services.governance_store import (
    GovernanceTransitionError,
    get_or_create,
    reset_governance_store_for_tests,
    transition,
)


def _shortest_paths_from_unknown() -> dict[GovernanceState, list[GovernanceState]]:
    """BFS: sequence of transition targets from UNKNOWN to reach each state."""
    start = GovernanceState.UNKNOWN
    paths: dict[GovernanceState, list[GovernanceState]] = {start: []}
    q: deque[GovernanceState] = deque([start])
    while q:
        u = q.popleft()
        for v in allowed_targets(u):
            if v not in paths:
                paths[v] = paths[u] + [v]
                q.append(v)
    return paths


from typing import AsyncGenerator

@pytest.fixture(autouse=True)
async def _clean_store() -> AsyncGenerator[None, None]:
    await reset_governance_store_for_tests()
    yield
    await reset_governance_store_for_tests()


@pytest.mark.asyncio
async def test_get_or_create_twice_same_row() -> None:
    fqn = "service.db.schema.table"
    a = await get_or_create(fqn)
    b = await get_or_create(fqn)
    assert a is b
    assert a.state == GovernanceState.UNKNOWN


@pytest.mark.asyncio
async def test_happy_path_scan_to_approved() -> None:
    fqn = "db.schema.t1"
    await transition(fqn, GovernanceState.SCANNED)
    await transition(fqn, GovernanceState.SUGGESTED)
    r = await transition(fqn, GovernanceState.APPROVED, evidence="judge ok")
    assert r.state == GovernanceState.APPROVED
    assert r.last_evidence == "judge ok"


@pytest.mark.asyncio
async def test_happy_path_enforced_drift_remediated() -> None:
    fqn = "db.schema.t2"
    for s in (
        GovernanceState.SCANNED,
        GovernanceState.SUGGESTED,
        GovernanceState.APPROVED,
        GovernanceState.ENFORCED,
    ):
        await transition(fqn, s)
    await transition(fqn, GovernanceState.DRIFT_DETECTED)
    await transition(fqn, GovernanceState.REMEDIATED)
    r = await transition(fqn, GovernanceState.ENFORCED)
    assert r.state == GovernanceState.ENFORCED


@pytest.mark.asyncio
async def test_evidence_truncated_to_500() -> None:
    fqn = "db.schema.t3"
    await transition(fqn, GovernanceState.SCANNED)
    long_ev = "x" * 600
    r = await transition(fqn, GovernanceState.SUGGESTED, evidence=long_ev)
    assert r.last_evidence is not None
    assert len(r.last_evidence) == 500
    assert r.last_evidence.endswith("...")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("from_state", "illegal_to"),
    [
        (frm, to)
        for frm in GovernanceState
        for to in GovernanceState
        if to not in allowed_targets(frm)
    ],
)
async def test_illegal_transition_raises(
    from_state: GovernanceState, illegal_to: GovernanceState
) -> None:
    fqn = f"illegal.{from_state.value}.{illegal_to.value}"
    paths = _shortest_paths_from_unknown()
    assert from_state in paths, f"fixture cannot reach {from_state}"
    for step in paths[from_state]:
        await transition(fqn, step)
    with pytest.raises(GovernanceTransitionError) as exc:
        await transition(fqn, illegal_to)
    assert exc.value.from_state == from_state
    assert exc.value.to_state == illegal_to
    assert exc.value.fqn == fqn


@pytest.mark.asyncio
async def test_every_allowed_edge_succeeds() -> None:
    """Each entry in ALLOWED_TRANSITIONS is exercised at least once."""
    for frm, targets in ALLOWED_TRANSITIONS.items():
        for to in targets:
            fqn = f"edge.{frm.value}.{to.value}"
            await reset_governance_store_for_tests()
            for step in _shortest_paths_from_unknown()[frm]:
                await transition(fqn, step)
            r = await transition(fqn, to)
            assert r.state == to
