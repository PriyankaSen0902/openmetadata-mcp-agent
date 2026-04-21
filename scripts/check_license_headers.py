#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Verify every source file starts with the Apache 2.0 license header.

Used by Makefile target `make license-header-check` and by the CI security-scan
job. Mirrors OpenMetadata's `yarn license-header-fix` discipline.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files we check — Python + TS + JS source. Skip generated/vendored content.
SOURCE_PATTERNS = ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]
SKIP_PATH_PARTS = {
    ".git",
    ".idea",
    ".cursor",
    ".claude",
    ".vscode",
    "node_modules",
    "build",
    "dist",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# Substring that must appear in the first ~15 lines of every source file.
HEADER_MARKER = "Apache License, Version 2.0"


def is_skipped(path: Path) -> bool:
    return bool(set(path.parts) & SKIP_PATH_PARTS)


def has_header(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as fh:
            head = "".join([next(fh, "") for _ in range(15)])
    except (OSError, UnicodeDecodeError):
        return False
    return HEADER_MARKER in head


def main() -> int:
    missing: list[Path] = []
    checked = 0
    for pattern in SOURCE_PATTERNS:
        for path in ROOT.rglob(pattern):
            if is_skipped(path):
                continue
            if path.name == "__init__.py" and path.read_text(encoding="utf-8").strip() == "":
                continue
            checked += 1
            if not has_header(path):
                missing.append(path.relative_to(ROOT))

    if missing:
        print(
            f"FAIL: {len(missing)} of {checked} source file(s) missing license header:",
            file=sys.stderr,
        )
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        print("\nFix: prepend the contents of LICENSE_HEADER.txt to each file.", file=sys.stderr)
        return 1

    print(f"OK: license header present on all {checked} source file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
