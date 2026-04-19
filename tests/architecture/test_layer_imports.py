#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
"""Three Laws of Implementation Law 1: layer separation enforcement.

Per .idea/Plan/Architecture/CodingStandards.md:
  - api/ may import services/, models/, middleware/, observability/, config/
        but NOT clients/
  - services/ may import clients/, models/, observability/
        but NOT api/ or fastapi
  - clients/ may import models/, observability/, config/
        but NOT services/ or api/

Greppable: scans every .py file in src/copilot/ and asserts the rules.
This is a poor-man's import boundary checker; if we ever grow, swap in pydeps.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "copilot"


def _read_imports(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^\s*(?:from|import)\s+(copilot\.[\w.]+)", re.MULTILINE)
    return pattern.findall(text)


def _src_files(layer: str) -> list[Path]:
    layer_dir = SRC / layer
    if not layer_dir.exists():
        return []
    return [p for p in layer_dir.rglob("*.py") if p.name != "__init__.py"]


class TestApiLayer:
    """api/ may NOT import clients/ directly. Must go through services/."""

    def test_api_does_not_import_clients(self) -> None:
        violations: list[str] = []
        for path in _src_files("api"):
            for imp in _read_imports(path):
                if imp.startswith("copilot.clients"):
                    violations.append(f"{path.relative_to(ROOT)} imports {imp}")
        assert not violations, "api/ -> clients/ direct import:\n" + "\n".join(violations)


class TestServicesLayer:
    """services/ may NOT import api/ or fastapi. Must stay HTTP-agnostic."""

    def test_services_does_not_import_api(self) -> None:
        violations: list[str] = []
        for path in _src_files("services"):
            for imp in _read_imports(path):
                if imp.startswith("copilot.api"):
                    violations.append(f"{path.relative_to(ROOT)} imports {imp}")
        assert not violations, "services/ -> api/ import:\n" + "\n".join(violations)

    def test_services_does_not_import_fastapi(self) -> None:
        violations: list[str] = []
        pattern = re.compile(r"^\s*(?:from|import)\s+fastapi", re.MULTILINE)
        for path in _src_files("services"):
            text = path.read_text(encoding="utf-8")
            if pattern.search(text):
                violations.append(str(path.relative_to(ROOT)))
        assert not violations, "services/ leaks fastapi import:\n" + "\n".join(violations)


class TestClientsLayer:
    """clients/ may NOT import api/ or services/."""

    def test_clients_does_not_import_api(self) -> None:
        violations: list[str] = []
        for path in _src_files("clients"):
            for imp in _read_imports(path):
                if imp.startswith("copilot.api"):
                    violations.append(f"{path.relative_to(ROOT)} imports {imp}")
        assert not violations, "clients/ -> api/ import:\n" + "\n".join(violations)

    def test_clients_does_not_import_services(self) -> None:
        violations: list[str] = []
        for path in _src_files("clients"):
            for imp in _read_imports(path):
                if imp.startswith("copilot.services"):
                    violations.append(f"{path.relative_to(ROOT)} imports {imp}")
        assert not violations, "clients/ -> services/ import:\n" + "\n".join(violations)


class TestNoBannedImports:
    """No print() calls and no `requests` library anywhere in src/."""

    def test_no_print_in_src(self) -> None:
        violations: list[str] = []
        pattern = re.compile(r"^\s*print\s*\(", re.MULTILINE)
        for path in SRC.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if pattern.search(text):
                violations.append(str(path.relative_to(ROOT)))
        assert not violations, "print() in src/ (use structlog):\n" + "\n".join(violations)

    def test_no_requests_lib_in_src(self) -> None:
        violations: list[str] = []
        pattern = re.compile(r"^\s*(?:from|import)\s+requests\b", re.MULTILINE)
        for path in SRC.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if pattern.search(text):
                violations.append(str(path.relative_to(ROOT)))
        assert not violations, "requests lib in src/ (use httpx):\n" + "\n".join(violations)
