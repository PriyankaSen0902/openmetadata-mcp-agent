# =============================================================================
# Makefile for openmetadata-mcp-agent
#
# Naming convention: agent-specific targets are kebab-case-clear; OpenMetadata
# upstream contributors will recognize aliases like install_dev_env, py_format,
# static-checks below.
# =============================================================================

.DEFAULT_GOAL := help
.PHONY: help setup install install_dev_env install_ui install-hooks \
        om-start om-stop om-health om-logs om-gen-token \
        demo demo-cached demo-fresh \
        restart-agent test test-unit test-integration test-security test-arch \
        lint py_format static-checks license-header-check pre-commit-all ci-local clean

# -----------------------------------------------------------------------------
# Help (default target)
# -----------------------------------------------------------------------------
help:
	@echo "openmetadata-mcp-agent — common targets"
	@echo ""
	@echo "  Setup:"
	@echo "    make setup                Copy .env.example -> .env if missing (then edit secrets)"
	@echo "    make install              Install runtime + dev dependencies (agent + UI)"
	@echo "    make install_dev_env      Alias for 'make install' (matches OM upstream Makefile)"
	@echo "    make install_ui           Install UI dependencies only"
	@echo "    make install-hooks        Install + run pre-commit hooks (required before first commit)"
	@echo ""
	@echo "  OpenMetadata (local OM at :8585):"
	@echo "    make om-start            Start OpenMetadata + MySQL + Elasticsearch"
	@echo "    make om-stop             Stop and remove OpenMetadata containers"
	@echo "    make om-health           Check if OpenMetadata health endpoint is responding"
	@echo "    make om-logs             Tail OpenMetadata server logs"
	@echo "    make om-gen-token        Generate Bot JWT for AI_SDK_TOKEN (.env)"
	@echo "    (load_seed / trigger_om_search_reindex load repo .env automatically)"
	@echo ""
	@echo "  Run:"
	@echo "    make demo                 Start agent backend + UI for live demo"
	@echo "    make demo-cached          Start agent in --demo-mode (serves pre-cached responses)"
	@echo "    make demo-fresh           Drop seed data, reload, restart everything"
	@echo "    make restart-agent        Restart only the agent backend"
	@echo ""
	@echo "  Quality gates:"
	@echo "    make test                 Run all tests (unit + security + architecture)"
	@echo "    make test-unit            Run unit tests only (<10s)"
	@echo "    make test-integration     Run integration tests (requires running OM container)"
	@echo "    make test-security        Run security tests (prompt injection, SC-N claims)"
	@echo "    make test-arch            Run architecture tests (Three Laws layer enforcement)"
	@echo "    make lint                 Run ruff lint check"
	@echo "    make py_format            Format Python with ruff (alias for OM contributors)"
	@echo "    make static-checks        Run mypy --strict (alias for OM contributors)"
	@echo "    make license-header-check Verify every source file has Apache 2.0 header"
	@echo "    make pre-commit-all       Run every pre-commit hook against every file"
	@echo "    make ci-local             Run the full CI suite locally"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean                Remove build artifacts, caches"

# -----------------------------------------------------------------------------
# Install
# -----------------------------------------------------------------------------
setup:
	@test -f .env && echo ".env already exists — not overwriting. Edit it with real secrets." || cp .env.example .env
	@test -f .env && echo "Next: edit .env (AI_SDK_TOKEN, OPENAI_API_KEY). Never commit .env." || echo "Created .env from .env.example — edit AI_SDK_TOKEN and OPENAI_API_KEY before make demo."

install:
	pip install -e ".[dev]"
	@$(MAKE) install_ui
	@echo "Installed. Next: make setup && edit .env; then make demo"

install_dev_env: install   ## Alias for OpenMetadata-upstream contributors

install_ui:
	@if [ -d "ui" ]; then cd ui && npm ci; fi

install-hooks:
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	pre-commit install
	pre-commit run --all-files
	@echo "Pre-commit hooks installed and clean."

# -----------------------------------------------------------------------------
# OpenMetadata local instance
# -----------------------------------------------------------------------------
om-start:
	@bash scripts/start_om.sh

om-stop:
	@echo "Stopping OpenMetadata stack ..."
	docker compose -f infrastructure/docker-compose.om.yml down
	@echo "OpenMetadata stopped."

om-health:
	@curl -sf http://localhost:8586/healthcheck >/dev/null && echo " ← OM healthy (admin healthcheck)" || echo "OM not reachable (try :8585 / :8586)"

om-logs:
	docker compose -f infrastructure/docker-compose.om.yml logs -f openmetadata-server

om-gen-token:
	@python scripts/generate_bot_jwt.py

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
demo:
	@echo "Starting agent backend on http://127.0.0.1:8000 ..."
	uvicorn copilot.api.main:app --host 127.0.0.1 --port 8000 --reload &
	@if [ -d "ui" ]; then echo "Starting UI on http://localhost:3000 ..."; cd ui && npm run dev; fi

demo-cached:
	COPILOT_DEMO_MODE=cached uvicorn copilot.api.main:app --host 127.0.0.1 --port 8000

demo-fresh:
	@echo "Dropping seed data and reloading ..."
	python scripts/load_seed.py --drop-existing
	@echo "Triggering OpenMetadata search reindex (tables may not appear in search_metadata until ES catches up) ..."
	@python scripts/trigger_om_search_reindex.py || echo "WARNING: search reindex failed — run scripts/trigger_om_search_reindex.py manually after OM is healthy."
	@$(MAKE) restart-agent

restart-agent:
	@pkill -f "uvicorn copilot.api.main:app" || true
	@sleep 1
	uvicorn copilot.api.main:app --host 127.0.0.1 --port 8000 --reload &
	@echo "Agent restarted."

# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------
test:
	pytest

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v -m integration

test-security:
	pytest tests/security -v -m security

test-arch:
	pytest tests/architecture -v

# -----------------------------------------------------------------------------
# Quality gates
# -----------------------------------------------------------------------------
lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

py_format:   ## Alias for OpenMetadata-upstream contributors
	ruff format src/ tests/

static-checks:   ## Alias for OpenMetadata-upstream contributors (OM uses basedpyright; we use mypy)
	mypy --strict src/copilot

license-header-check:
	@python scripts/check_license_headers.py

pre-commit-all:
	pre-commit run --all-files

ci-local:
	@$(MAKE) pre-commit-all
	@$(MAKE) lint
	@$(MAKE) static-checks
	@$(MAKE) license-header-check
	@$(MAKE) test-unit
	@$(MAKE) test-security
	@$(MAKE) test-arch
	# Known CVEs in Phase 1 pinned deps — tracked for post-hackathon bump
	# in the dep-maintenance issue (@5009226-bhawikakumari). Each ignore
	# here MUST be paired with an entry in that tracking issue. Do NOT
	# extend this list without updating the issue.
	pip-audit --skip-editable \
		--ignore-vuln CVE-2026-34070 \
		--ignore-vuln GHSA-r7w7-9xr2-qq2r \
		--ignore-vuln GHSA-fv5p-p927-qmxr \
		--ignore-vuln CVE-2026-28277 \
		--ignore-vuln CVE-2025-64439 \
		--ignore-vuln CVE-2026-27794 \
		--ignore-vuln CVE-2025-71176 \
		--ignore-vuln CVE-2025-62727
	bandit -r src/copilot -ll
	@if [ -d "ui" ]; then \
		NPM_PATH="$$(command -v npm 2>/dev/null || echo none)"; \
		case "$$NPM_PATH" in \
			/mnt/*|none) echo "[ci-local] Skipping ui/ build: need Linux-native npm on PATH (got: $$NPM_PATH). Real CI runs this in a Node container; install nodejs in WSL to run it locally." ;; \
			*) cd ui && npm run build && npx tsc --noEmit ;; \
		esac; \
	fi
	@echo "All CI gates passed locally."

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} + 2>/dev/null || true
