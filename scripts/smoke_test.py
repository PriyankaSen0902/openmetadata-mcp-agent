#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Demo-day morning smoke test: verify backend is up + responding correctly.

Used by .idea/Plan/Project/Runbook.md "Demo-day morning checklist".

Exit code:
    0  all green; safe to record/demo
    1  agent backend down or returning unexpected response
    2  OpenMetadata MCP server unreachable (when --include-om is set)
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def check_url(url: str, expected_key: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"FAIL: {url} unreachable: {exc}", file=sys.stderr)
        return False

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"FAIL: {url} returned non-JSON: {body[:200]}", file=sys.stderr)
        return False

    if expected_key not in data:
        print(f"FAIL: {url} missing key {expected_key!r}: {data}", file=sys.stderr)
        return False

    print(f"OK: {url}  ({expected_key}={data[expected_key]})")
    return True


def check_chat(url: str) -> bool:
    req = urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps({"message": "show me some tables"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"FAIL: {url} unreachable or error: {exc}", file=sys.stderr)
        # Try to read the error body if it's an HTTPError
        if hasattr(exc, "read"):
            print(f"Error body: {exc.read().decode('utf-8')[:500]}", file=sys.stderr)
        return False

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"FAIL: {url} returned non-JSON: {body[:200]}", file=sys.stderr)
        return False

    if "response" not in data or not data["response"]:
        print(f"FAIL: {url} missing or empty 'response': {data}", file=sys.stderr)
        return False

    audit_log = data.get("audit_log", [])
    if not any(entry.get("success") is True for entry in audit_log):
        print(f"FAIL: {url} audit_log missing a successful entry: {audit_log}", file=sys.stderr)
        print(
            "HINT: Read uvicorn stderr for agent.execute_tool.failed / om.call_tool.failed "
            "(full MCP error text). If tables exist in OM but search is empty, run "
            "`python scripts/trigger_om_search_reindex.py` and wait ~30-120s, then retry.",
            file=sys.stderr,
        )
        return False

    print(f"OK: {url}  (agent responded and recorded a successful tool call)")
    print("--- Agent Response ---")
    print(data["response"])
    print("----------------------")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo-day smoke test.")
    parser.add_argument("--agent-url", default="http://127.0.0.1:8000")
    parser.add_argument("--om-url", default="http://localhost:8585")
    parser.add_argument(
        "--include-om", action="store_true", help="Also check OpenMetadata server health"
    )
    args = parser.parse_args()

    print("smoke: agent backend ...")
    if not check_url(f"{args.agent_url}/api/v1/healthz", "status"):
        return 1

    if args.include_om:
        print("smoke: openmetadata server ...")
        if not check_url(f"{args.om_url}/api/v1/system/version", "version"):
            return 2

        print("smoke: agent chat endpoint ...")
        if not check_chat(f"{args.agent_url}/api/v1/chat"):
            return 3

    print("smoke: all green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
