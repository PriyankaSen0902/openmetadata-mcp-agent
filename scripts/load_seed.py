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
"""Load the frozen seed dataset into a running OpenMetadata instance.

Reads seed/customer_db.json and uses the OM REST API to create:
  1. A database service (if missing)
  2. A database (customer_db)
  3. A database schema (public)
  4. All tables defined in the seed file

Idempotent: re-runs update existing entities without erroring.

Usage:
    python scripts/load_seed.py               # idempotent upsert
    python scripts/load_seed.py --drop-existing  # delete first, then load
    python scripts/load_seed.py --om-url http://host:8585  # custom OM URL

``AI_SDK_TOKEN`` is read from the process environment or from the repo root
``.env`` (loaded automatically via ``python-dotenv``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
SEED_FILE = ROOT / "seed" / "customer_db.json"

DEFAULT_OM_URL = "http://localhost:8585"
API_PREFIX = "/api/v1"
SERVICE_NAME = "customer_db_service"
SERVICE_TYPE = "CustomDatabase"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# OpenMetadata 1.6+ requires dataLength for these column types when creating tables via API.
_NEEDS_DATA_LENGTH = frozenset({"CHAR", "VARCHAR", "BINARY", "VARBINARY", "TEXT"})
_DEFAULT_DATA_LENGTH: dict[str, int] = {
    "VARCHAR": 255,
    "CHAR": 36,
    "BINARY": 16,
    "VARBINARY": 255,
    "TEXT": 65535,
}


def _get_headers(token: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_request(
    url: str,
    *,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Make an HTTP request to the OM REST API with basic retry logic."""
    body = json.dumps(data).encode("utf-8") if data else None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)  # noqa: S310
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 409:
                parsed = json.loads(response_body) if response_body else {}
                print(f"  (already exists, skipping: {parsed.get('message', '')})")
                return parsed
            if exc.code == 404 and method == "DELETE":
                print("  (not found, nothing to delete)")
                return None
            if attempt == MAX_RETRIES:
                print(
                    f"FAIL: {method} {url} -> HTTP {exc.code}: {response_body[:300]}",
                    file=sys.stderr,
                )
                return None
            print(f"  retry {attempt}/{MAX_RETRIES} after HTTP {exc.code}...")
            time.sleep(RETRY_DELAY_SECONDS)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == MAX_RETRIES:
                print(f"FAIL: {method} {url} -> {exc}", file=sys.stderr)
                return None
            print(f"  retry {attempt}/{MAX_RETRIES} after {type(exc).__name__}...")
            time.sleep(RETRY_DELAY_SECONDS)
    return None


def _get_or_create(
    base_url: str,
    entity_type: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """Create an entity via PUT (upsert semantics)."""
    url = f"{base_url}{API_PREFIX}/{entity_type}"
    return _api_request(url, method="PUT", data=payload, headers=headers)


def _coerce_data_length(data_type: str, col_def: dict[str, Any]) -> int | None:
    """Return dataLength for OM when required; None for types that do not need it."""
    dt = (data_type or "").upper()
    if dt not in _NEEDS_DATA_LENGTH:
        return None
    explicit = col_def.get("dataLength")
    if explicit is not None:
        return int(explicit)
    return _DEFAULT_DATA_LENGTH.get(dt, 255)


def _build_column_payload(col_def: dict[str, Any]) -> dict[str, Any]:
    """Convert a seed column definition to an OM CreateColumn shape."""
    data_type = col_def.get("dataType", "VARCHAR")
    column: dict[str, Any] = {
        "name": col_def["name"],
        "dataType": data_type,
    }
    data_length = _coerce_data_length(data_type, col_def)
    if data_length is not None:
        column["dataLength"] = data_length
    desc = col_def.get("description", "")
    if desc:
        column["description"] = desc

    tags = col_def.get("tags", [])
    if tags:
        column["tags"] = [
            {"tagFQN": tag, "source": "Classification", "labelType": "Manual"} for tag in tags
        ]
    return column


def _delete_tables(
    base_url: str,
    schema_fqn: str,
    table_names: list[str],
    headers: dict[str, str],
) -> int:
    """Delete tables by FQN. Returns the number of tables deleted."""
    deleted = 0
    for name in table_names:
        fqn = f"{schema_fqn}.{name}"
        url = f"{base_url}{API_PREFIX}/tables/name/{fqn}?hardDelete=true"
        result = _api_request(url, method="DELETE", headers=headers)
        if result is not None:
            deleted += 1
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the frozen seed dataset into OM.")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Delete all seed tables before loading (used by `make demo-fresh`)",
    )
    parser.add_argument(
        "--om-url",
        default=os.environ.get("AI_SDK_HOST", DEFAULT_OM_URL),
        help=f"OpenMetadata server URL (default: {DEFAULT_OM_URL})",
    )
    args = parser.parse_args()

    if not SEED_FILE.exists():
        print(f"ERROR: {SEED_FILE} not found", file=sys.stderr)
        return 1

    token = os.environ.get("AI_SDK_TOKEN", "")
    headers = _get_headers(token)
    base_url = args.om_url.rstrip("/")

    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    tables = seed.get("tables", [])
    db_name = seed.get("database", "customer_db")
    schema_name = seed.get("schema", "public")

    print(f"seed: read {len(tables)} table(s) from {SEED_FILE}")

    if not tables:
        print("seed: empty dataset; nothing to load")
        return 0

    # Step 1: Create database service
    print(f"seed: ensuring database service '{SERVICE_NAME}' ...")
    svc_payload = {
        "name": SERVICE_NAME,
        "serviceType": SERVICE_TYPE,
        "connection": {"config": {"type": SERVICE_TYPE}},
    }
    svc = _get_or_create(base_url, "services/databaseServices", svc_payload, headers)
    if svc is None:
        print("ERROR: failed to create database service", file=sys.stderr)
        return 1

    # Step 2: Create database
    print(f"seed: ensuring database '{db_name}' ...")
    db_payload = {
        "name": db_name,
        "service": SERVICE_NAME,
    }
    db = _get_or_create(base_url, "databases", db_payload, headers)
    if db is None:
        print("ERROR: failed to create database", file=sys.stderr)
        return 1

    # Step 3: Create schema
    schema_fqn = f"{SERVICE_NAME}.{db_name}.{schema_name}"
    print(f"seed: ensuring schema '{schema_fqn}' ...")
    schema_payload = {
        "name": schema_name,
        "database": f"{SERVICE_NAME}.{db_name}",
    }
    schema = _get_or_create(base_url, "databaseSchemas", schema_payload, headers)
    if schema is None:
        print("ERROR: failed to create database schema", file=sys.stderr)
        return 1

    # Step 4: Optionally drop existing tables
    if args.drop_existing:
        print(f"seed: dropping {len(tables)} existing table(s) ...")
        table_names = [t["name"] for t in tables]
        deleted = _delete_tables(base_url, schema_fqn, table_names, headers)
        print(f"seed: deleted {deleted} table(s)")

    # Step 5: Create tables
    created = 0
    failed = 0
    for table_def in tables:
        tbl_name = table_def["name"]
        print(f"seed: upserting table '{schema_fqn}.{tbl_name}' ...")

        columns = [_build_column_payload(c) for c in table_def.get("columns", [])]

        tbl_payload: dict[str, Any] = {
            "name": tbl_name,
            "databaseSchema": schema_fqn,
            "columns": columns,
            "tableType": "Regular",
        }

        desc = table_def.get("description", "")
        if desc:
            tbl_payload["description"] = desc

        tags = table_def.get("tags", [])
        if tags:
            tbl_payload["tags"] = [
                {"tagFQN": tag, "source": "Classification", "labelType": "Manual"} for tag in tags
            ]

        result = _get_or_create(base_url, "tables", tbl_payload, headers)
        if result is not None:
            created += 1
        else:
            failed += 1

    print(f"\nseed: done — {created} table(s) created/updated, {failed} failed")
    print(f"seed: --drop-existing={args.drop_existing}")

    if failed > 0:
        print(f"WARNING: {failed} table(s) failed to load", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
