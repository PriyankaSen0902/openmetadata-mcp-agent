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
"""Governance API routes.

Per .idea/Plan/Architecture/APIContract.md:
  - GET /api/v1/governance/drift  returns current drift findings
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from copilot.middleware.error_envelope import _envelope
from copilot.models.chat import ErrorCode
from copilot.observability import get_logger
from copilot.services.drift import get_latest_snapshot

log = get_logger(__name__)

router = APIRouter(tags=["governance"])


@router.get("/governance/drift", summary="List current governance drift findings")
async def get_drift(_request: Request) -> JSONResponse:
    """Return the latest drift scan results.

    Returns 200 with drift items on success.
    Returns 503 with structured error if OM was unreachable during the last scan.
    """
    snapshot = get_latest_snapshot()

    # If the last scan hit an MCP error, return 503 per APIContract
    if snapshot.error is not None:
        log.info("governance.drift.unavailable", error=snapshot.error)
        return _envelope(ErrorCode.OM_UNAVAILABLE, _request)

    payload = {
        "drift": [asdict(item) for item in snapshot.items],
        "scanned_at": snapshot.scanned_at,
        "entity_count": snapshot.entity_count,
        "drift_count": len(snapshot.items),
        "ts": datetime.now(UTC).isoformat(),
    }

    return JSONResponse(status_code=200, content=payload)
