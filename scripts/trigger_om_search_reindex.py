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
"""Trigger OpenMetadata Elasticsearch search reindex (after API-only seed loads).

Tables created via ``load_seed.py`` exist in the catalog but may not appear in
``GET /api/v1/search/query`` until search indices are rebuilt. Use this script
(or ``make demo-fresh`` which invokes it) so ``search_metadata`` MCP has data.

Usage:
    python scripts/trigger_om_search_reindex.py
    python scripts/trigger_om_search_reindex.py --om-url http://host:8585

Requires ``AI_SDK_TOKEN`` (Bot JWT): set in the process environment or in the
repo root ``.env`` (loaded automatically via ``python-dotenv``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_PREFIX = "/api/v1"


def main() -> int:
    parser = argparse.ArgumentParser(description="POST OpenMetadata search reindex.")
    parser.add_argument(
        "--om-url",
        default=os.environ.get("AI_SDK_HOST", "http://localhost:8585").rstrip("/"),
        help="OpenMetadata base URL (default: AI_SDK_HOST or http://localhost:8585)",
    )
    args = parser.parse_args()

    token = os.environ.get("AI_SDK_TOKEN", "")
    if not token:
        print("ERROR: AI_SDK_TOKEN is not set", file=sys.stderr)
        return 1

    # OM 1.6.x: search indexing is the "SearchIndexingApplication" app, not /search/reindex.
    primary = f"{args.om_url}{API_PREFIX}/apps/trigger/SearchIndexingApplication"
    fallback = f"{args.om_url}{API_PREFIX}/search/reindex"
    body = json.dumps({"recreateIndex": False, "batchSize": 100}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    def _post(url: str) -> tuple[int, str]:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            return -1, str(exc)

    status, raw = _post(primary)
    url_used = primary

    if status == 404:
        status, raw = _post(fallback)
        url_used = fallback

    if status == -1:
        print(f"FAIL: POST {url_used} -> {raw}", file=sys.stderr)
        return 1

    if status >= 400:
        if status == 400 and "already running" in raw.lower():
            print(f"OK: search indexing job already running ({url_used})")
            return 0
        print(f"FAIL: POST {url_used} -> HTTP {status}: {raw[:800]}", file=sys.stderr)
        return 1

    print(f"OK: search indexing triggered ({url_used})")
    if raw.strip():
        print(raw[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
