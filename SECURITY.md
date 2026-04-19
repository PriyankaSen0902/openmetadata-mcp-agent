# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in `openmetadata-mcp-agent`, please report it privately. **Do NOT open a public GitHub issue.**

### How to report

Email **gunapalanivel@gmail.com** (project maintainer) with:

1. A description of the issue (what is broken)
2. Steps to reproduce, including any required inputs (sanitized — no real secrets)
3. The attacker model (anonymous user / authenticated catalog editor / CI attacker / supply-chain) — see [`.idea/Plan/Security/ThreatModel.md`](.idea/Plan/Security/ThreatModel.md) for our defined attacker types
4. Impact assessment if you have one (data exposure, write capability, denial of service, etc.)
5. Your suggested fix if you have one

We will acknowledge within 48 hours and aim to resolve within 7 days for P0/P1 issues.

## Supported versions

| Version | Status |
|---------|--------|
| `0.1.x` (Phase 1 hackathon scaffold) | Pre-release; security fixes on best-effort basis |
| `0.2.x` (Phase 2 core features) | Active |
| `0.3.x` (Phase 3 polish) | Active |
| Anything older | Unsupported — upgrade |

## Security architecture

This project's security posture is documented across these planning docs (most published in this repo):

- [`.idea/Plan/Security/ThreatModel.md`](.idea/Plan/Security/ThreatModel.md) — security claims (SC-1..SC-10), entrypoints (ENTRY-N), sensitive sinks, secret flow, trust boundary diagram
- [`.idea/Plan/Security/PromptInjectionMitigation.md`](.idea/Plan/Security/PromptInjectionMitigation.md) — Module G five-layer defense for the LLM agent boundary
- [`.idea/Plan/Security/ControlCoverage.md`](.idea/Plan/Security/ControlCoverage.md) — 9-area control coverage matrix
- [`.idea/Plan/Security/SecretsHandling.md`](.idea/Plan/Security/SecretsHandling.md) — `AI_SDK_TOKEN`, `OPENAI_API_KEY`, `GITHUB_TOKEN` policy
- [`.idea/Plan/Security/CIHardening.md`](.idea/Plan/Security/CIHardening.md) — GitHub Actions workflow hardening (read-all default permissions, SHA-pinned actions, dependabot)

### Key security guarantees (claimed; verifiable in code)

| ID | Claim |
|----|-------|
| SC-1 | FastAPI binds to `127.0.0.1` only (loopback) in v1 |
| SC-2 | Three secrets via env (`AI_SDK_TOKEN`, `OPENAI_API_KEY`, `GITHUB_TOKEN`); never logged; never committed |
| SC-3 | Every LLM-suggested write tool call requires explicit user confirmation via `POST /api/v1/chat/confirm` |
| SC-4 | LLM JSON output is Pydantic-validated against `ToolCallProposal` before any tool execution |
| SC-5 | LLM cannot call any tool outside the 13-tool allowlist (12 OM + 1 GitHub MCP) |
| SC-6 | Catalog content is HTML-escaped + truncated to ≤500 chars before insertion into LLM prompts |
| SC-7 | Every external call has timeout + retry-with-backoff + circuit breaker |
| SC-8 | Error responses never include API keys, JWTs, file paths, full prompts, or raw exceptions |
| SC-9 | No `pickle.load`, `joblib.load`, `yaml.load(unsafe)`, `eval`, `exec`, `os.system` anywhere |
| SC-10 | No upstream OpenMetadata code modifications (we use only the public `data-ai-sdk`) |

Each claim has a corresponding `tests/security/test_*.py` test. Verify yourself: `make test`.

## What is NOT in scope (v1)

These are documented as out-of-scope for the hackathon timeline. They are NOT vulnerabilities for this version:

- Multi-tenant isolation (single-user demo)
- Network-attacker scenarios (FastAPI is loopback-only)
- DoS / load-test resilience beyond the documented `slowapi` rate limits
- HSM/Vault for production secret rotation (`.env` is fine for laptop deployment)
- Pen test (deferred to post-Phase-3)

If you find an issue in one of these areas, it is a feature request, not a vulnerability — open a regular issue.

## Coordinated disclosure

We follow standard 90-day coordinated disclosure. After we ship a fix:

1. We credit the reporter (with permission) in `CHANGELOG.md`.
2. We publish the issue + fix details after the fix is released.
3. We backport to the supported version range above.

Thanks for helping keep this project safe.
