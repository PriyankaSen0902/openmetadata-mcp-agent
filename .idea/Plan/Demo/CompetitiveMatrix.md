# Competitive Matrix — Hackathon T-01 Lens

> **Purpose**: Honest positioning for internal rehearsal — not for public trash-talk. Refresh weekly during the sprint (TaskSync **P1-20**, **P2-18**).

**Legend:** Strong / Partial / Weak / Unknown (mark **Unknown** when judging from public artifacts only).

## Rows (criteria from hackathon brief)

| Criterion                | Us (`openmetadata-mcp-agent`)                                        | LangGraph-style orchestration (e.g. @0xSaksham public prototype) | Claude + MCP chaining demo (e.g. @thisisvaishnav Loom) |
| ------------------------ | -------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------ |
| Potential impact         | **Strong** (target: governance + HITL writes + drift story)          | Partial–Strong (varies by depth of OM writes)                    | Partial (often read-heavy assistants)                  |
| Creativity & innovation  | **Strong** (governance FSM + catalog write-back + Multi-MCP Phase 3) | Strong (orchestration is table stakes)                           | Partial–Strong                                         |
| Technical excellence     | **Partial** until CI + tests + coverage gates green                  | Unknown                                                          | Unknown                                                |
| Best use of OpenMetadata | **Strong** (12 tools, typed + string-callable; seed 50+ tables)      | Partial–Strong                                                   | Partial–Strong                                         |
| User experience          | **Partial** until OM-native UI (P3-10) + HITL modal (P2-12)          | Unknown                                                          | Strong (polished Loom)                                 |
| Presentation quality     | **Partial** (README GIF + video pending)                             | Unknown                                                          | Strong                                                 |

## Differentiators to prove in demo

1. **Human-in-the-loop** on `patch_entity` with API contract (`pending_confirmation`), not ad-hoc tool runs.
2. **Governance state in catalog** (when [GovernanceEngine.md](../FeatureDev/GovernanceEngine.md) P2-22 ships).
3. **Drift without being asked** (P2-23 / P2-24).
4. **Multi-MCP** (Phase 3): OM → GitHub issue per PII table.

## How to update this file

1. Re-watch / skim linked public demos (2 min each).
2. Adjust **Unknown → Partial/Strong** only with evidence.
3. Add date + one-line “what changed” at bottom.

---

_Last refreshed: 2026-04-23 — initial matrix from plan sync._
