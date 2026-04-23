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
"""Per-entity governance lifecycle state + FSM edges (P2-20).

Canonical transition map per .idea/Plan/FeatureDev/GovernanceEngine.md.
"""

from __future__ import annotations

from enum import StrEnum


class GovernanceState(StrEnum):
    """Governance lifecycle states for one catalog entity (FQN)."""

    UNKNOWN = "unknown"
    SCANNED = "scanned"
    SUGGESTED = "suggested"
    APPROVED = "approved"
    ENFORCED = "enforced"
    DRIFT_DETECTED = "drift_detected"
    REMEDIATED = "remediated"


ALLOWED_TRANSITIONS: dict[GovernanceState, frozenset[GovernanceState]] = {
    GovernanceState.UNKNOWN: frozenset({GovernanceState.SCANNED}),
    GovernanceState.SCANNED: frozenset({GovernanceState.SUGGESTED, GovernanceState.UNKNOWN}),
    GovernanceState.SUGGESTED: frozenset({GovernanceState.APPROVED, GovernanceState.SCANNED}),
    GovernanceState.APPROVED: frozenset({GovernanceState.ENFORCED, GovernanceState.DRIFT_DETECTED}),
    GovernanceState.ENFORCED: frozenset({GovernanceState.DRIFT_DETECTED}),
    GovernanceState.DRIFT_DETECTED: frozenset(
        {GovernanceState.REMEDIATED, GovernanceState.SUGGESTED}
    ),
    GovernanceState.REMEDIATED: frozenset({GovernanceState.ENFORCED}),
}


def allowed_targets(state: GovernanceState) -> frozenset[GovernanceState]:
    """Return states reachable in one step from ``state``."""
    return ALLOWED_TRANSITIONS[state]
