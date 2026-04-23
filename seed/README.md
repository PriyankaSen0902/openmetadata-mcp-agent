# Seed Data

Frozen demo dataset for `openmetadata-mcp-agent`. Loaded into the local OpenMetadata instance via `scripts/load_seed.py` so the demo is reproducible without an internet connection or stable upstream catalog state.

## Files

- `customer_db.json` — 50+ tables across `customer_db.public.*` (populated in BUILD Phase 2 task P1-13)

## Composition target (per BUILD Phase 2)

| Bucket                          | Count | Purpose                                                                            |
| ------------------------------- | ----- | ---------------------------------------------------------------------------------- |
| Normal tables                   | 30    | Realistic catalog noise (orders, products, sessions, ...)                          |
| PII-containing tables           | 12    | Auto-classification demo target (email, phone, SSN, address)                       |
| Lineage-rich tables             | 5     | Lineage impact demo (orders -> order_items -> products)                            |
| Prompt-injection-planted tables | 2     | Module G defense demo (column descriptions contain instruction-injection patterns) |
| Tier1 critical                  | 1     | Lineage impact "critical asset at risk" demo                                       |

## Loading

```bash
# Idempotent; re-running updates timestamps without erroring.
python scripts/load_seed.py

# To drop and reload (used by `make demo-fresh`):
python scripts/load_seed.py --drop-existing
```

Verify after load:

```bash
# Prefer explicit from/size — some OM 1.6.x builds error on q=*&index=...&size=1 alone.
curl "http://localhost:8585/api/v1/search/query?q=%2A&index=table_search_index&from=0&size=10" \
  -H "Authorization: Bearer ${AI_SDK_TOKEN}" \
  | jq '.hits.total.value'
# Should print 50 or more.
```

If that still returns HTTP 500, try a minimal query (wildcard URL-encoded):

```bash
curl "http://localhost:8585/api/v1/search/query?q=%2A&index=table_search_index" \
  -H "Authorization: Bearer ${AI_SDK_TOKEN}" \
  | jq '.hits.total.value'
```

If the total is `0` but `GET /api/v1/tables` returns rows, Elasticsearch search indices are not populated yet (API seed does not always index immediately). Run `python scripts/trigger_om_search_reindex.py` and wait ~30-120s, then re-check the curl above.

## Why frozen

The demo runs against the same dataset every time so:

1. Benchmarks (time, precision, cost) are reproducible across rehearsals.
2. The hero GIF captures consistent screen content.
3. The prompt-injection demo target column has known content the agent has been tested against.
4. Judges who clone the repo can `make demo` and see the same thing the team rehearsed.
