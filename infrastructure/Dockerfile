# =============================================================================
# Dockerfile for openmetadata-mcp-agent backend
#
# Multi-stage build: install -> runtime. Final image is slim Python with the
# agent code + runtime deps only. UI is built separately via `cd ui && npm run build`.
# =============================================================================

# ---- Builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir .

# ---- Runtime ----
FROM python:3.11-slim AS runtime

# Add curl for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Run as non-root
RUN useradd --create-home --shell /bin/bash agent
USER agent
WORKDIR /home/agent

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/copilot /usr/local/bin/copilot

EXPOSE 8000

CMD ["copilot"]
