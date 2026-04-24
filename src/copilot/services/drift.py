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
"""Drift detection service — detects divergence from approved governance baseline.

Per .idea/Plan/FeatureDev/GovernanceEngine.md:
  - Hash signal: SHA-256 of (description, columns, tags) detects field changes.
  - Tag signal: expected governance tags missing or unexpected tags added.

This module is pure business logic: NO HTTP types, NO direct SDK calls.
Calls ``copilot.clients.om_mcp`` for data fetching.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from copilot.clients import om_mcp
from copilot.middleware.error_envelope import McpUnavailable
from copilot.observability import get_logger

log = get_logger(__name__)


class DriftSignal(StrEnum):
    """Type of drift detected on an entity."""

    HASH_CHANGED = "hash_changed"
    TAG_MISSING = "tag_missing"
    TAG_UNEXPECTED = "tag_unexpected"


@dataclass(frozen=True)
class DriftItem:
    """One drift finding for one entity."""

    entity_fqn: str
    entity_type: str
    signal: DriftSignal
    detail: str
    detected_at: str  # ISO-8601


@dataclass
class DriftSnapshot:
    """In-memory snapshot of the latest drift scan results."""

    items: list[DriftItem] = field(default_factory=list)
    scanned_at: str | None = None
    entity_count: int = 0
    error: str | None = None


# Module-level mutable state — drift results cached between polls.
_baseline: dict[str, str] = {}  # fqn → hash
_latest_snapshot = DriftSnapshot()


def get_latest_snapshot() -> DriftSnapshot:
    """Return the most recent drift scan results (read-only view)."""
    return _latest_snapshot


def _hash_entity(entity: dict[str, Any]) -> str:
    """Produce a stable SHA-256 hash of governance-relevant entity fields."""
    relevant = {
        "description": entity.get("description", "") or "",
        "columns": sorted(
            [
                {
                    "name": c.get("name", ""),
                    "dataType": c.get("dataType", ""),
                    "tags": sorted(
                        [t.get("tagFQN", "") for t in (c.get("tags") or [])],
                    ),
                }
                for c in (entity.get("columns") or [])
            ],
            key=lambda c: c["name"],
        ),
        "tags": sorted([t.get("tagFQN", "") for t in (entity.get("tags") or [])]),
    }
    blob = json.dumps(relevant, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def _extract_tag_fqns(entity: dict[str, Any]) -> set[str]:
    """Extract all tag FQNs from an entity (top-level + column-level)."""
    tags: set[str] = set()
    for t in entity.get("tags") or []:
        fqn = t.get("tagFQN", "")
        if fqn:
            tags.add(fqn)
    for col in entity.get("columns") or []:
        for t in col.get("tags") or []:
            fqn = t.get("tagFQN", "")
            if fqn:
                tags.add(fqn)
    return tags


# Expected governance tag prefixes — entities that had these at baseline
# should still have them.
_GOVERNANCE_TAG_PREFIXES = ("PII.", "Tier.", "PersonalData.")


def detect_drift(
    entity_fqn: str,
    entity_type: str,
    current: dict[str, Any],
    baseline_hash: str | None,
    baseline_tags: set[str] | None = None,
) -> list[DriftItem]:
    """Pure function: compare current entity state to baseline and return drift items.

    Args:
        entity_fqn: Fully-qualified name of the entity.
        entity_type: Entity type (e.g. "table").
        current: Full entity dict from OM.
        baseline_hash: SHA-256 hash from previous scan, or None if first scan.
        baseline_tags: Set of tag FQNs from previous scan.

    Returns:
        List of DriftItem findings (may be empty).
    """
    now = datetime.now(UTC).isoformat()
    items: list[DriftItem] = []

    current_hash = _hash_entity(current)

    # Signal 1: Hash changed
    if baseline_hash is not None and current_hash != baseline_hash:
        items.append(
            DriftItem(
                entity_fqn=entity_fqn,
                entity_type=entity_type,
                signal=DriftSignal.HASH_CHANGED,
                detail=f"Entity hash changed from {baseline_hash[:12]}… to {current_hash[:12]}…",
                detected_at=now,
            )
        )

    # Signal 2: Tag drift (only if we have a baseline to compare against)
    if baseline_tags is not None:
        current_tags = _extract_tag_fqns(current)

        # Governance tags that were present in baseline but are now missing
        items.extend(
            DriftItem(
                entity_fqn=entity_fqn,
                entity_type=entity_type,
                signal=DriftSignal.TAG_MISSING,
                detail=f"Governance tag '{tag}' was removed",
                detected_at=now,
            )
            for tag in baseline_tags
            if any(tag.startswith(p) for p in _GOVERNANCE_TAG_PREFIXES) and tag not in current_tags
        )

        # Governance tags that appeared but were not in baseline
        items.extend(
            DriftItem(
                entity_fqn=entity_fqn,
                entity_type=entity_type,
                signal=DriftSignal.TAG_UNEXPECTED,
                detail=f"New governance tag '{tag}' appeared",
                detected_at=now,
            )
            for tag in current_tags
            if any(tag.startswith(p) for p in _GOVERNANCE_TAG_PREFIXES) and tag not in baseline_tags
        )

    return items


# ---------------------------------------------------------------------------
# Baseline store (in-memory, keyed by fqn)
# ---------------------------------------------------------------------------

_baseline_hashes: dict[str, str] = {}
_baseline_tags: dict[str, set[str]] = {}


async def run_drift_scan() -> DriftSnapshot:
    """Execute one drift scan: fetch entities, compare to baseline, update state.

    Calls ``om_mcp.call_tool("search_metadata", ...)`` via asyncio.to_thread
    to avoid blocking the event loop.

    Returns:
        The new DriftSnapshot (also stored in module-level ``_latest_snapshot``).
    """
    global _latest_snapshot

    log.info("drift.scan.start")
    now = datetime.now(UTC).isoformat()

    try:
        # Fetch all tables (up to 100 for v1 per NFR-02)
        search_result = await asyncio.to_thread(
            om_mcp.call_tool,
            "search_metadata",
            {"query": "*", "limit": 100},
        )
    except McpUnavailable as exc:
        log.warning("drift.scan.mcp_unavailable", error=str(exc))
        _latest_snapshot = DriftSnapshot(
            scanned_at=now,
            error="OpenMetadata is temporarily unreachable",
        )
        return _latest_snapshot

    # Normalise search results to a list of hits
    hits = search_result.get("hits", search_result.get("data", []))
    if isinstance(hits, dict):
        hits = hits.get("hits", [])

    drift_items: list[DriftItem] = []
    scanned = 0

    for hit in hits:
        fqn = hit.get("fullyQualifiedName", hit.get("fqn", ""))
        entity_type = hit.get("entityType", "table")
        if not fqn:
            continue

        try:
            entity = await asyncio.to_thread(
                om_mcp.call_tool,
                "get_entity_details",
                {"fqn": fqn, "entity_type": entity_type},
            )
        except McpUnavailable:
            log.warning("drift.scan.entity_fetch_failed", fqn=fqn)
            continue

        scanned += 1
        current_hash = _hash_entity(entity)
        current_tags = _extract_tag_fqns(entity)

        # Detect drift against baseline
        findings = detect_drift(
            entity_fqn=fqn,
            entity_type=entity_type,
            current=entity,
            baseline_hash=_baseline_hashes.get(fqn),
            baseline_tags=_baseline_tags.get(fqn),
        )
        drift_items.extend(findings)

        # Update baseline for next scan
        _baseline_hashes[fqn] = current_hash
        _baseline_tags[fqn] = current_tags

    _latest_snapshot = DriftSnapshot(
        items=drift_items,
        scanned_at=now,
        entity_count=scanned,
    )

    log.info(
        "drift.scan.complete",
        entities_scanned=scanned,
        drift_count=len(drift_items),
    )
    return _latest_snapshot


def reset_state() -> None:
    """Reset all module-level state. For testing only."""
    global _latest_snapshot
    _baseline_hashes.clear()
    _baseline_tags.clear()
    _latest_snapshot = DriftSnapshot()
