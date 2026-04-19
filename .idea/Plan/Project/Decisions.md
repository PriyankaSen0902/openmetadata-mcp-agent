# Architecture Decision Records (ADR)

## ADR-01: Standalone Python Project vs Java McpTool Extension

**Status**: Accepted
**Date**: 2026-04-19
**Context**: The hackathon rules state "You must build a new project; simply modifying an existing codebase is not permitted." The existing `openmetadata-mcp` is a Java module with no LLM dependencies.
**Decision**: Build a standalone Python project that connects to OM's MCP server as a client.
**Alternatives Rejected**:

- Java McpTool extension: Violates hackathon rules, no LLM deps in pom.xml, 30+ min build cycles
- TypeScript: Python has better LLM ecosystem, official `data-ai-sdk` is Python
  **Consequences**: Faster iteration (Python), uses official SDK, demo-independent from OM builds.

---

## ADR-02: Track T-01 (MCP Ecosystem) + T-06 (Governance) Hybrid

**Status**: Accepted
**Date**: 2026-04-19
**Context**: T-01 (MCP) is the highest-value track. T-06 (Governance) has unclaimed issues. A project spanning both tracks demonstrates breadth.
**Decision**: Primary track T-01 with organic T-06 coverage via auto-classification and governance summary.
**Consequences**: Judges see depth (MCP orchestration) + breadth (governance). Two major issues addressed (#26645, #26608).

---

## ADR-03: LLM Provider Selection

**Status**: ✅ Confirmed
**Date**: 2026-04-19
**Context**: Agent logic needs an LLM for NL understanding, tool selection, classification, and response generation. Team received **free OpenAI API credits** via the OpenAI Codex Hackathon Bengaluru (April 17, 2026).
**Decision**: **OpenAI GPT-4o-mini** for all agent logic. **GPT-4o** for demo recording (higher quality responses).
**Rationale**:

- Free API credits available — zero cost blocker
- Best-documented function calling in LangChain/LangGraph ecosystem
- GPT-4o-mini at $0.15/1M input tokens enables hundreds of governance scans
- Judges likely use OpenAI themselves — familiar output quality
  **Packages**: `langchain-openai`, `openai`
  **Env var**: `OPENAI_API_KEY` (from platform.openai.com promotions page)

---

## ADR-04: Using `data-ai-sdk` (Official OM Python SDK)

**Status**: Accepted
**Date**: 2026-04-19
**Context**: Research confirmed OpenMetadata publishes `data-ai-sdk` on PyPI — a Python SDK that wraps the MCP server with LangChain tool adapters.
**Decision**: Use `data-ai-sdk` as the primary MCP client.
**Consequences**: Native auth handling, LangChain integration, maintained by OM team. Minimizes boilerplate.

---

## ADR-05: LangGraph for Agent Orchestration

**Status**: Accepted
**Date**: 2026-04-19
**Context**: Need a Python agent framework that supports stateful multi-step workflows, tool routing, and human-in-the-loop.
**Decision**: Use LangGraph for agent orchestration.
**Alternatives Rejected**:

- Raw LLM API calls: No state management, no tool routing
- AutoGen: Heavier, less MCP-native
- CrewAI: Less control over agent flow
  **Consequences**: Clean graph-based workflows, native LangChain tool support via `langchain-mcp-adapters`.

---

## ADR-06: React Chat UI

**Status**: Accepted
**Date**: 2026-04-19
**Context**: Need a demo-friendly UI. Judges can interact live.
**Decision**: React (Vite) with OM-native styling (purple `#7147E8`, dark mode). Color verified in [openmetadata-ui/src/main/resources/ui/src/styles/variables.less](../../../openmetadata-ui/src/main/resources/ui/src/styles/variables.less).
**Alternatives Rejected**:

- CLI only: Less impressive for demo
- Slack bot: Harder to demo live, auth complexity
  **Consequences**: Visual demo, fast iteration, OM-aligned branding.

---

## ADR-07: Prompt-Injection Mitigation Strategy (Module G)

**Status**: Accepted
**Date**: 2026-04-19
**Context**: Our agent reads catalog content (column descriptions, table descriptions, glossary terms) from OpenMetadata and inserts that content into LLM prompts to make classification + governance decisions. Catalog content is **attacker-controlled**: any user with edit permission on a table can plant a prompt-injection payload. This is the same class of bug that gitar-bot flagged on competitor PR [#27506](https://github.com/open-metadata/OpenMetadata/pull/27506) ("user content interpolated into LLM prompt"). We will not repeat this.
**Decision**: Five-layer defense:

1. **Input neutralization** — `services/prompt_safety.neutralize()` escapes HTML/markdown, tags instruction-injection patterns with `[SUSPICIOUS:]`, strips zero-width Unicode, truncates to ≤500 chars per field
2. **Structured-message prompt assembly** — system instructions in `system` role; catalog content in `user` role; never concatenated into one string
3. **Output schema validation** — every LLM tool-call response parsed via `ToolCallProposal.model_validate()`; failures return 502 `llm_invalid_output`
4. **Tool allowlist enforcement** — service layer checks `tool_name in ALLOWED_TOOLS` (13 tools) even after Pydantic `Literal` constraint
5. **HITL confirmation gate** — every `soft_write` or `hard_write` tool call requires explicit user confirmation via `POST /chat/confirm`
   **Alternatives Rejected**:

- Trust the LLM to follow instructions (the documented industry failure mode)
- LLM-side guardrails only (e.g. system-prompt warnings) — defeated by indirect injection
- Allowlist-only (no input escaping) — leaves the LLM open to misclassification even when output is constrained
  **Consequences**: Three independent failure modes; an attacker must defeat all five to cause a wrong write. Documented in [Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md). Demo Moment 3 in [JudgePersona.md](./JudgePersona.md) showcases the defense live.

---

## ADR-08: Observability Stack

**Status**: Accepted
**Date**: 2026-04-19
**Context**: Per [Feature-Dev SKILL §Architect's Judgment Rule 6](../../agents/Feature-Dev/SKILL.md): "observability is architecture, not a feature". Sriharsha-persona judge ([JudgePersona.md](./JudgePersona.md)) is likely to ask "show me the request_id flow from the chat UI through to the OM patch_entity log line" and expects a real answer.
**Decision**:

- **Logging**: `structlog` 24+ with JSON formatter; rotating file at `logs/agent.log` (10 MB × 5); custom redaction processor strips known secret values from log lines per [Security/SecretsHandling.md](../Security/SecretsHandling.md)
- **Metrics**: `prometheus-client` exposing `GET /api/v1/metrics` with the 4 Golden Signals (Latency / Traffic / Errors / Saturation) plus token usage + circuit-breaker state per [Architecture/APIContract.md §GET /api/v1/metrics](../Architecture/APIContract.md)
- **Correlation**: `request_id` UUID generated by middleware on every HTTP request, bound to `structlog.contextvars`, propagated through every tool call, every log line, every error envelope
  **Alternatives Rejected**:
- Plain `logging` module — no structured fields, no contextvars
- Datadog / New Relic — paid tools, account setup overhead, no value for a hackathon demo
- OpenTelemetry tracing — added complexity not justified at v1 scale; structlog output is OTel-compatible if a collector is added later
  **Consequences**: Judges can hit `/metrics` live during the demo (per [JudgePersona.md §Moment 2](./JudgePersona.md)); same `request_id` visible across UI devtools, server logs, and Prometheus labels; logs are PII-safe by construction.
