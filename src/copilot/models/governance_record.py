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
"""One row per entity FQN under governance (P2-20)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from copilot.models.governance_state import GovernanceState


def _now_utc() -> datetime:
    return datetime.now(UTC)


class EntityGovernanceRecord(BaseModel):
    """In-memory governance row keyed by ``fqn`` in ``governance_store``."""

    model_config = ConfigDict(frozen=True)

    fqn: str = Field(min_length=1, max_length=2048)
    state: GovernanceState = GovernanceState.UNKNOWN
    updated_at: datetime = Field(default_factory=_now_utc)
    lineage_snapshot_hash: str | None = None
    approved_tags: frozenset[str] = Field(default_factory=frozenset)
    last_evidence: str | None = Field(default=None, max_length=500)

    @field_validator("approved_tags", mode="before")
    @classmethod
    def _coerce_approved_tags(cls, value: Any) -> frozenset[str]:
        if value is None:
            return frozenset()
        if isinstance(value, frozenset):
            return value
        if isinstance(value, (list, tuple, set)):
            return frozenset(str(x) for x in value)
        return frozenset()
