#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Phase 3 minimal happy-path demo: Multi-MCP cross-platform workflow.

Creates a GitHub issue from an OM-derived list.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


def call_chat(url: str, message: str, session_id: str | None = None) -> dict[str, Any]:
    print(f"\n[User] -> {message}")
    data = {"message": message}
    if session_id:
        data["session_id"] = session_id
        
    req = urllib.request.Request(
        f"{url}/api/v1/chat",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"FAIL: /api/v1/chat error: {exc}", file=sys.stderr)
        if hasattr(exc, "read"):
            print(f"Error body: {exc.read().decode('utf-8')[:500]}", file=sys.stderr)
        sys.exit(1)


def confirm_proposal(url: str, session_id: str, proposal_id: str) -> dict[str, Any]:
    print(f"\n[System] Confirming proposal {proposal_id}...")
    req = urllib.request.Request(
        f"{url}/api/v1/chat/confirm",
        data=json.dumps({
            "session_id": session_id,
            "proposal_id": proposal_id,
            "accepted": True
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"FAIL: /api/v1/chat/confirm error: {exc}", file=sys.stderr)
        if hasattr(exc, "read"):
            print(f"Error body: {exc.read().decode('utf-8')[:500]}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-MCP cross-platform demo.")
    parser.add_argument("--agent-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    url = args.agent_url
    print(f"Starting Multi-MCP Demo against {url}")
    
    # Step 1: Send the cross-MCP query
    query = "Find tables related to customers and create a GitHub issue in mock/repo to add PII tags to them."
    res = call_chat(url, query)
    
    print(f"\n[Agent] <- {res.get('response', '')}")
    
    pending = res.get("pending_confirmation")
    if not pending:
        print("FAIL: Expected a pending confirmation for github_create_issue, but got none.", file=sys.stderr)
        print(json.dumps(res, indent=2))
        return 1
        
    tool_name = pending.get("tool_name")
    proposal_id = pending.get("proposal_id")
    session_id = res.get("session_id")
    
    print(f"\n[Gate] Action required: {tool_name} (Risk: {pending.get('risk_level')})")
    print(f"[Gate] Arguments: {json.dumps(pending.get('arguments'), indent=2)}")
    
    if tool_name != "github_create_issue":
        print(f"FAIL: Expected github_create_issue, got {tool_name}", file=sys.stderr)
        return 1
        
    time.sleep(1)  # tiny pause for dramatic effect
    
    # Step 2: Confirm the proposal
    confirm_res = confirm_proposal(url, session_id, proposal_id)
    print(f"\n[Agent] <- {confirm_res.get('response', '')}")
    
    audit_log = confirm_res.get("audit_log", [])
    if not audit_log or not audit_log[0].get("success"):
        print("FAIL: The tool execution was not successful.", file=sys.stderr)
        return 1
        
    print("\n✅ Multi-MCP workflow completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
