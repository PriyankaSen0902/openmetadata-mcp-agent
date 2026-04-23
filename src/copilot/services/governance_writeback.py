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

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from copilot.clients import om_mcp
from copilot.models.governance_state import GovernanceState
from copilot.observability import get_logger

log = get_logger(__name__)


async def enqueue_writeback_for_state(
    *,
    entity_fqn: str,
    governance_state: GovernanceState,
    base_patch_arguments: dict[str, Any],
) -> None:
    """Fire-and-forget write-back for governance states backed by patch_entity."""
    payload = _build_patch_entity_arguments(
        base_patch_arguments=base_patch_arguments,
        governance_state=governance_state,
    )
    task = asyncio.create_task(
        _execute_patch_entity(entity_fqn=entity_fqn, arguments=payload),
        name=f"governance-writeback:{entity_fqn}:{governance_state.value}",
    )
    task.add_done_callback(_log_background_failure)


def _build_patch_entity_arguments(
    *,
    base_patch_arguments: dict[str, Any],
    governance_state: GovernanceState,
) -> dict[str, Any]:
    args = dict(base_patch_arguments)
    patch = list(args.get("patch", [])) if isinstance(args.get("patch"), list) else []

    patch.append(
        {
            "op": "add",
            "path": "/extension/governance_state",
            "value": governance_state.value,
        }
    )
    patch.append(
        {
            "op": "add",
            "path": "/extension/governance_approved_tags_json",
            "value": json.dumps(
                _extract_approved_tags(base_patch_arguments),
                separators=(",", ":"),
            ),
        }
    )
    patch.append(
        {
            "op": "add",
            "path": "/extension/governance_lineage_snapshot_hash",
            "value": _extract_lineage_hash(base_patch_arguments),
        }
    )
    args["patch"] = patch
    return args


async def _execute_patch_entity(*, entity_fqn: str, arguments: dict[str, Any]) -> None:
    start = datetime.now(UTC)
    try:
        await asyncio.to_thread(om_mcp.call_tool, "patch_entity", arguments)
        duration_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
        log.info(
            "governance.writeback.success",
            entity_fqn=entity_fqn,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        duration_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
        log.warning(
            "governance.writeback.failed",
            entity_fqn=entity_fqn,
            duration_ms=duration_ms,
            error=str(exc),
        )
        raise


def _log_background_failure(task: asyncio.Task[None]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is None:
        return
    log.warning("governance.writeback.task_failed", error=str(exc))


def _extract_approved_tags(arguments: dict[str, Any]) -> list[str]:
    tags = arguments.get("approved_tags")
    if isinstance(tags, list):
        return [str(tag) for tag in tags]
    return []


def _extract_lineage_hash(arguments: dict[str, Any]) -> str:
    value = arguments.get("lineage_snapshot_hash")
    if isinstance(value, str):
        return value
    return ""
