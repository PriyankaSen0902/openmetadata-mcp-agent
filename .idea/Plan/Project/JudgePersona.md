# Judge Personas — Demo Moments

> **Public figures named in [README.md](../README.md) vision section** (Suresh Srinivas, Sriharsha Chintalapani): treat as **distributed-systems + metadata-native** judges — they reward **contracts**, **failure behavior**, and **real OM depth**, not slideware.

## Three judge archetypes

| Archetype                | What they care about                               | What they click                                                         |
| ------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------- |
| **Platform engineer**    | APIs, errors, logs, idempotency, HITL              | Swagger `/api/v1/docs`, `POST /chat`, `POST /chat/confirm`, network tab |
| **Data governance lead** | Tagging, lineage, policy, catalog truth            | OM UI: table metadata, lineage tab, classification/tags                 |
| **AI skeptic**           | Prompt injection, hallucinated tools, data leakage | Malicious-ish queries from seed, inspect redaction / allowlist          |

## Moment 1 — “This is not a wrapper”

**Audience:** All three.
**Action:** Open Swagger or README Mermaid — show **LangGraph** boundary + **MCP** allowlist + **structured error envelope**.
**Pass:** One sentence naming **two** concrete OM MCP tools used in the last request.

## Moment 2 — “OpenMetadata is the source of truth”

**Audience:** Governance lead + platform.
**Action:** Same entity in **chat** and **OM UI** — FQN matches; tags or summary align after refresh.
**Pass:** Judge copies FQN from UI into a second chat query and gets a consistent answer.

## Moment 3 — “Adversarial default”

**Audience:** AI skeptic (+ primary hackathon security story).
**Action:** Drive the **planted prompt-injection** path from [`seed/customer_db.json`](../../seed/customer_db.json) per [Demo/Narrative.md §Scene 3](../Demo/Narrative.md).
**Pass:** E2E or live demo shows **sanitized** rendering + **no** execution of hidden instructions; CI **`tests/security/test_prompt_injection.py`** referenced as backstop.

## Anti-patterns (do not do these on camera)

- Reading API keys or JWTs from screen.
- `dangerouslySetInnerHTML` or raw HTML from model output.
- Claiming “we use all 12 tools” without a **named** list or audit reference ([DataFindings/ExistingMCPAudit.md](../DataFindings/ExistingMCPAudit.md)).
- Apologizing for local-only demo without showing **why** (ThreatModel v1 loopback binding).

## Post–governance engine (P2-19+)

Add **Moment 4** (optional, 20 s): open OM entity **custom properties** — show `governance_state` (or agreed key) written by the agent after approval or drift ([GovernanceEngine.md](../FeatureDev/GovernanceEngine.md)).

---

## Extended profiles (public sources)

> Sources: public bios from [getcollate.io/about](https://www.getcollate.io/about) and OpenMetadata GitHub committer history.

### Persona 1 — Suresh Srinivas (CEO, Co-Founder)

| Field                                | Value                                                                                                                                                                                                             |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Background**                       | Hadoop committer; co-founded Hortonworks (acquired by Cloudera); former Chief Architect for Data at Uber                                                                                                          |
| **Domain depth**                     | Distributed systems, data platforms at hyperscale, OSS governance                                                                                                                                                 |
| **What he likes (signal)**           | Real-world data team usability; system thinking; "this would actually work in a Fortune 500" maturity; correct API usage; respect for the schema-first design                                                     |
| **What turns him off (anti-signal)** | LLM novelty without engineering rigor; toy demos; broken builds; "AI slop" code with no error handling; submissions that fork OM internals instead of using the public surface                                    |
| **Question he is likely to ask**     | "How does this hold up if a column description contains an injection attack?" or "What happens when the OM MCP server returns 503?"                                                                               |
| **Our answer must show**             | The Module-G prompt-injection mitigation ([Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md)) and the circuit-breaker behavior in [NFRs.md §The 5 Things AI Never Adds](./NFRs.md) |

### Persona 2 — Sriharsha Chintalapani (CTO, Co-Founder)

| Field                                | Value                                                                                                                                                                                                                |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Background**                       | Apache Kafka + Storm PMC member; previously Architect at Uber and Hortonworks; engineering lead at Mozilla and Yahoo!; "highly scalable distributed systems" specialist                                              |
| **Domain depth**                     | Streaming, event-driven systems, code quality, build/test discipline                                                                                                                                                 |
| **What he likes (signal)**           | Clean code; layer separation; structured logging; tests; ADRs; reproducible builds; commits that read like a real engineer wrote them                                                                                |
| **What turns him off (anti-signal)** | `print()` debugging in submitted code; uncaught exceptions in demo flow; dependencies pinned to `latest`; `git add .` commit history                                                                                 |
| **Question he is likely to ask**     | "Show me the request_id flow from the chat UI through to the OM patch_entity log line" or "Where do you handle a malformed LLM JSON response?"                                                                       |
| **Our answer must show**             | The end-to-end correlation ID in [NFRs.md §NFR-06 Observability](./NFRs.md) and the Pydantic validation gate in [Security/PromptInjectionMitigation.md §Output validation](../Security/PromptInjectionMitigation.md) |

### Persona 3 — Hackathon Track Maintainer (@PubChimps)

| Field                    | Value                                                                                                                                                                      |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Role**                 | Posted all six hackathon idea issues; comments on most submission threads                                                                                                  |
| **Behaviors observed**   | Will not assign issues; comments "thanks for the PR!" politely on every submission; flags PRs through the standard `safe-to-test` review path                                  |
| **What he likes (signal)** | Submissions that solve a real OM gap; respect for the existing MCP surface; PRs that are reviewable end-to-end                                                             |
| **What turns him off (anti-signal)** | Spam; multiple competing claims for the same idea; submissions that ignore @PubChimps's clarifying comments                                                                |
| **Our handling**         | Post a single intent comment on #26645 and #26608 (template in [TaskSync.md](../TaskSync.md) Phase 0); link the standalone repo + demo video on submission day; never spam |

### Persona 4 — Bot reviewers (Gitar, Copilot, github-actions)

| Field                  | Value                                                                                                                                                                                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Role**               | Run on every upstream PR (we observed gitar-bot's review on competitor PR [#27506](https://github.com/open-metadata/OpenMetadata/pull/27506))                                                                                           |
| **What they catch**    | Prompt injection ("user content interpolated into LLM prompt"), division by zero, security claims contradicted by code, unpinned dependencies                                                                                           |
| **Implication for us** | Even though our standalone repo is OUTSIDE the OpenMetadata monorepo (no gitar-bot review), the JUDGES will read the bot reviews on competitors' PRs. We score points by FIXING the same class of bugs the bots flagged on competitors. |
| **Concrete win**       | Our [Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md) explicitly cites and mitigates the exact issue gitar-bot caught on PR #27506 — judges who read both PRs will see we did our homework              |

## What we will NOT do (because it scores zero with this panel)

| Anti-pattern                                        | Why it loses points                                                                                                                 |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Lead the demo with "look at our cool LLM"           | Suresh and Sriharsha both spent decades on data platforms; they are not impressed by LLM novelty alone                              |
| Skip error handling because "it's just a hackathon" | Sriharsha will spot a `try: ... except: pass` from across the room                                                                  |
| Use `latest` dep versions                           | Builds break on demo day; bot reviews flag it as supply-chain risk                                                                  |
| Pre-record the entire demo                          | "Live demo or it didn't happen" energy; but we DO have a backup recording per [Demo/FailureRecovery.md](../Demo/FailureRecovery.md) |
| Submit without a runbook                            | Suresh has run on-call rotations at Uber; absence of `docs/runbook.md` is a tell                                                    |
| Promise "production-ready" then ship `print()`      | Worse than not promising at all                                                                                                     |

## Cross-references

- Demo script: [Demo/Narrative.md](../Demo/Narrative.md)
- Backup if demo breaks: [Demo/FailureRecovery.md](../Demo/FailureRecovery.md)
- The actual mitigation: [Security/PromptInjectionMitigation.md](../Security/PromptInjectionMitigation.md)
- Competitive matrix the judges will compare us against: [Demo/CompetitiveMatrix.md](../Demo/CompetitiveMatrix.md)
