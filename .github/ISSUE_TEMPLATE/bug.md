---
name: Bug report
about: Something is broken
title: "[bug] "
labels: ["bug"]
assignees: []
---

## What happened

<!-- One paragraph: what you expected vs what happened -->

## Steps to reproduce

1.
2.
3.

## Environment

- **Phase**: <!-- 1 / 2 / 3 / 4 -->
- **OS**: <!-- Windows 11 / macOS 14 / Linux (which distro) -->
- **Python version**: <!-- output of `python --version` -->
- **OpenMetadata version**: <!-- output of `curl http://localhost:8585/api/v1/system/version` -->
- **Branch / commit**: <!-- output of `git rev-parse --short HEAD` -->

## Logs

<!-- Paste the relevant section from `logs/agent.log` (`structlog` JSON lines).
     Include the `request_id` if you can find it. SCRUB any secrets first. -->

```
<paste log here>
```

## Error envelope (if from API)

<!-- The `code`, `message`, `request_id`, `ts` from the JSON error response -->

```json
{ "code": "...", "message": "...", "request_id": "...", "ts": "..." }
```

## Severity

<!-- P0 = blocks demo; P1 = blocks current Phase exit gate; P2 = visible roughness; P3 = nice to have -->

- [ ] P0 — blocks demo
- [ ] P1 — blocks Phase exit
- [ ] P2 — visible bug, doesn't block
- [ ] P3 — minor

## Suggested fix (optional)

<!-- If you've already debugged it -->
