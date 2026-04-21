#!/usr/bin/env bash
# =============================================================================
# start_om.sh — Start the local OpenMetadata container stack and wait for
# the health endpoint to report healthy.
#
# Copyright 2026 Collate Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

set -euo pipefail

COMPOSE_FILE="infrastructure/docker-compose.om.yml"
HEALTH_URL="http://localhost:8585/api/v1/health"
MAX_RETRIES=40
RETRY_INTERVAL=5

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

check_prerequisites() {
    if ! command -v docker &>/dev/null; then
        error "Docker is not installed or not in PATH."
        error "Install from https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker compose version &>/dev/null; then
        error "Docker Compose V2 is not available."
        error "Update Docker or install the compose plugin."
        exit 1
    fi

    if ! docker info &>/dev/null 2>&1; then
        error "Docker daemon is not running. Start Docker Desktop or the daemon."
        exit 1
    fi
}

start_stack() {
    info "Starting OpenMetadata stack from ${COMPOSE_FILE} ..."
    docker compose -f "${COMPOSE_FILE}" up -d
    info "Containers started. Waiting for OpenMetadata to become healthy ..."
}

wait_for_health() {
    local attempt=1
    while [ "${attempt}" -le "${MAX_RETRIES}" ]; do
        if curl -sf "${HEALTH_URL}" 2>/dev/null | grep -q "healthy"; then
            echo ""
            info "OpenMetadata is healthy at ${HEALTH_URL}"
            return 0
        fi
        printf "\r  Waiting... attempt %d/%d (next check in %ds)" \
            "${attempt}" "${MAX_RETRIES}" "${RETRY_INTERVAL}"
        sleep "${RETRY_INTERVAL}"
        attempt=$((attempt + 1))
    done

    echo ""
    error "OpenMetadata did not become healthy after $((MAX_RETRIES * RETRY_INTERVAL))s."
    error "Check logs: docker compose -f ${COMPOSE_FILE} logs openmetadata-server"
    exit 1
}

print_next_steps() {
    echo ""
    info "============================================"
    info "  OpenMetadata is running at :8585"
    info "============================================"
    echo ""
    echo "  UI:      http://localhost:8585"
    echo "  Login:   admin / admin"
    echo "  Health:  curl ${HEALTH_URL}"
    echo ""
    echo "  Next steps:"
    echo "    1. Generate a Bot JWT (Settings → Bots → ingestion-bot)"
    echo "    2. Paste into .env as AI_SDK_TOKEN=<token>"
    echo "    3. Run: make demo"
    echo ""
    echo "  Stop OM:  make om-stop"
    echo "  Logs:     make om-logs"
    echo ""
}

main() {
    info "OpenMetadata local setup — openmetadata-mcp-agent"
    echo ""
    check_prerequisites
    start_stack
    wait_for_health
    print_next_steps
}

main "$@"
