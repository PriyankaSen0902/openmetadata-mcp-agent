#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Stub: report estimated remaining OpenAI credits for the configured key.

Used by .idea/Plan/Project/Runbook.md "Demo-day morning checklist" R-01.
OpenAI's billing API is org-scoped and not always queryable per-key, so this
ends up estimating from usage logs. For Phase 1 it just asserts the key is
present and looks well-formed; full quota check lands when needed.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        print("FAIL: OPENAI_API_KEY not set in environment", file=sys.stderr)
        return 1
    if not key.startswith("sk-"):
        print(
            "FAIL: OPENAI_API_KEY does not look like a real OpenAI key (no 'sk-' prefix)",
            file=sys.stderr,
        )
        return 1
    print(f"OK: OPENAI_API_KEY present (sk-***{key[-4:]})")
    print("note: full quota query implementation pending (Phase 3 task).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
