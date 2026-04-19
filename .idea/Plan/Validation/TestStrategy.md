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

| Module | Tests | Owner |
|--------|-------|-------|
| MCP Client wrapper | Tool call, auth, error handling | OMH-PSTL |
| Intent classifier | Route NL to correct tool | OMH-PSTL |
| Response formatter | Markdown table, lineage summary | OMH-PSTL |
| PII classifier | Column classification logic | OMH-GSA |
| Patch builder | JSON Patch construction | OMH-GSA |

## Integration Tests

| Scenario | Tools Involved | Owner |
|----------|---------------|-------|
| NL search → results | `search_metadata` | OMH-PSTL |
| Semantic search → results | `semantic_search` | OMH-PSTL |
| Entity details → formatted | `get_entity_details` | OMH-PSTL |
| Auto-classify → tags applied | `search` → `get_entity` → `patch_entity` | OMH-GSA |
| Lineage impact → report | `get_entity_lineage` | OMH-GSA |
| Chat → agent → response | Full pipeline with mock MCP | OMH-ATL |

## E2E Tests

| Test | Description | Owner |
|------|-------------|-------|
| Chat to search | Type query in UI → see results | OMH-ATL |
| Chat to classify | Trigger classification → see tags applied | OMH-GSA |
| Chat to lineage | Ask impact question → see report | OMH-GSA |

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires mock MCP)
pytest tests/integration/ -v

# E2E tests (requires running OM Docker)
pytest tests/e2e/ -v

# Full suite
pytest --cov=copilot --cov-report=html
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
- [ ] Test coverage >60%
