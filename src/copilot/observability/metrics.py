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
"""Prometheus metrics: 4 Golden Signals + token usage + circuit-breaker state.

Series and labels per .idea/Plan/Architecture/APIContract.md GET /api/v1/metrics.
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Use a dedicated registry so tests can construct fresh instances.
REGISTRY = CollectorRegistry()

# ----------------------------------------------------------------------------
# 4 Golden Signals
# ----------------------------------------------------------------------------

agent_requests_total = Counter(
    "agent_requests_total",
    "Total HTTP requests handled by the agent backend.",
    labelnames=("endpoint", "status_code"),
    registry=REGISTRY,
)

agent_errors_total = Counter(
    "agent_errors_total",
    "Total errors returned by the agent backend, labeled by error code.",
    labelnames=("code",),
    registry=REGISTRY,
)

agent_request_latency_seconds = Histogram(
    "agent_request_latency_seconds",
    "HTTP request latency in seconds.",
    labelnames=("endpoint",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 30.0),
    registry=REGISTRY,
)

# ----------------------------------------------------------------------------
# LLM and MCP call instrumentation
# ----------------------------------------------------------------------------

agent_llm_tokens_used_total = Counter(
    "agent_llm_tokens_used_total",
    "Total OpenAI tokens used.",
    labelnames=("direction", "model"),
    registry=REGISTRY,
)

agent_llm_calls_total = Counter(
    "agent_llm_calls_total",
    "Total OpenAI calls.",
    labelnames=("model", "outcome"),
    registry=REGISTRY,
)

agent_mcp_calls_total = Counter(
    "agent_mcp_calls_total",
    "Total MCP tool calls.",
    labelnames=("tool_name", "outcome"),
    registry=REGISTRY,
)

# ----------------------------------------------------------------------------
# Saturation: circuit-breaker state + active sessions + pending confirmations
# ----------------------------------------------------------------------------

agent_circuit_breaker_state = Gauge(
    "agent_circuit_breaker_state",
    "0=closed, 1=open, 2=half-open",
    labelnames=("circuit",),
    registry=REGISTRY,
)

agent_pending_confirmations = Gauge(
    "agent_pending_confirmations",
    "Currently-pending HITL confirmation proposals.",
    registry=REGISTRY,
)

agent_active_sessions = Gauge(
    "agent_active_sessions",
    "Currently-active chat sessions in memory.",
    registry=REGISTRY,
)


def render_prometheus_text() -> tuple[bytes, str]:
    """Return (payload, content_type) for the /metrics endpoint."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
