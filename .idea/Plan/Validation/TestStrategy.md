# Validation & Test Strategy

## Test Pyramid

```
         /‾‾‾‾‾‾‾‾‾‾\
        /  E2E Tests  \     ← 3-5 full workflow tests
       / (browser/chat) \
      /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
     / Integration Tests    \    ← 10-15 agent → MCP → mock OM
    /  (agent + mcp client)  \
   /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
  /     Unit Tests              \  ← 30-50 function-level tests
 /  (tools, formatters, logic)   \
```

## Unit Tests

| Module             | Tests                           | Owner    |
| ------------------ | ------------------------------- | -------- |
| MCP Client wrapper | Tool call, auth, error handling | OMH-PSTL |
| Intent classifier  | Route NL to correct tool        | OMH-PSTL |
| Response formatter | Markdown table, lineage summary | OMH-PSTL |
| PII classifier     | Column classification logic     | OMH-GSA  |
| Patch builder      | JSON Patch construction         | OMH-GSA  |

## Integration Tests

| Scenario                     | Tools Involved                           | Owner    |
| ---------------------------- | ---------------------------------------- | -------- |
| NL search → results          | `search_metadata`                        | OMH-PSTL |
| Semantic search → results    | `semantic_search`                        | OMH-PSTL |
| Entity details → formatted   | `get_entity_details`                     | OMH-PSTL |
| Auto-classify → tags applied | `search` → `get_entity` → `patch_entity` | OMH-GSA  |
| Lineage impact → report      | `get_entity_lineage`                     | OMH-GSA  |
| Chat → agent → response      | Full pipeline with mock MCP              | OMH-ATL  |

## E2E Tests

| Test             | Description                               | Owner   |
| ---------------- | ----------------------------------------- | ------- |
| Chat to search   | Type query in UI → see results            | OMH-ATL |
| Chat to classify | Trigger classification → see tags applied | OMH-GSA |
| Chat to lineage  | Ask impact question → see report          | OMH-GSA |

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires mock MCP)
pytest tests/integration/ -v

# E2E tests (requires running OM Docker)
pytest tests/e2e/ -v

# Full suite
pytest --cov=src/copilot --cov-report=html
```

## Acceptance Criteria (per phase)

### Phase 1

- [ ] MCP client connects to local OM
- [ ] `search_metadata("tables")` returns results
- [ ] Chat UI renders on localhost
- [ ] 10+ unit tests passing

### Phase 2

- [ ] NL query returns correct tool + results
- [ ] Auto-classification correctly tags 3+ PII columns
- [ ] Lineage impact report is human-readable
- [ ] 30+ unit tests, 5+ integration tests passing

### Phase 3

- [ ] All error cases handled gracefully
- [ ] UI is responsive and styled
- [ ] Demo video covers all 3 features
- [ ] Test coverage ≥70% on `src/copilot/` (align with [TaskSync.md](../TaskSync.md) P3-08 and [QualityGates.md](./QualityGates.md) Gate 0)

## Sixteen-issue engineering program — test mapping

Each **engineering** GitHub issue (see [FeatureDev/GovernanceEngine.md](../FeatureDev/GovernanceEngine.md), [TaskSync.md §Sixteen-issue](../TaskSync.md)) must list concrete tests in **Acceptance criteria** using [PR-Review/EngineeringIssueTemplate.md](../PR-Review/EngineeringIssueTemplate.md).

| Issue bucket                     | Unit                                                                 | Integration                            | E2E                                                                                         |
| -------------------------------- | -------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------- |
| #1–#2 Sessions + FSM             | `tests/unit/test_sessions.py`, `tests/unit/test_governance_store.py` | confirm/cancel with mock MCP           | —                                                                                           |
| #3–#4 Hooks + write-back + drift | store transitions, drift hash helpers                                | `tests/integration/` agent + respx MCP | —                                                                                           |
| #5 UX hardening                  | similarity pure fn, format_response helpers                          | agent classify with mock lineage       | —                                                                                           |
| #6–#8 Workflows                  | intent routing, patch builder                                        | full chat turn mock                    | —                                                                                           |
| #9–#11 FE                        | component tests if added                                             | API contract tests from UI             | —                                                                                           |
| #12 Multi-MCP                    | allowlist unit                                                       | mock second MCP server                 | optional                                                                                    |
| #13 Test + security              | extends `tests/security/`                                            | breaker-open paths                     | —                                                                                           |
| #14 CI                           | workflow dry-run                                                     | —                                      | —                                                                                           |
| #15 Demo automation              | seed loader already under `tests/unit/`                              | smoke `--include-om` optional          | —                                                                                           |
| **#16 E2E**                      | —                                                                    | —                                      | `tests/e2e/` Playwright: chat + HITL + [JudgePersona §Moment 3](../Project/JudgePersona.md) |
