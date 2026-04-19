#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Load the frozen seed dataset into a running OpenMetadata instance.

Stub for BUILD Phase 2 task P1-13. Reads seed/customer_db.json and POSTs each
table to OM via the REST API. Idempotent: re-runs update existing tables.

Usage:
    python scripts/load_seed.py               # idempotent upsert
    python scripts/load_seed.py --drop-existing  # delete first, then load
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "seed" / "customer_db.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the frozen seed dataset into OM.")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Delete all seed tables before loading (used by `make demo-fresh`)",
    )
    args = parser.parse_args()

    if not SEED_FILE.exists():
        print(f"ERROR: {SEED_FILE} not found", file=sys.stderr)
        return 1

    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    tables = seed.get("tables", [])
    print(f"seed: read {len(tables)} table(s) from {SEED_FILE}")

    if not tables:
        print("seed: empty dataset; nothing to load (Phase 1 placeholder)")
        return 0

    print("seed: load implementation pending (BUILD Phase 2 task P1-13)")
    print(f"seed: --drop-existing={args.drop_existing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
