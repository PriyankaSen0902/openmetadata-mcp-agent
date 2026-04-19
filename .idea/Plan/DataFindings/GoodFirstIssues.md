# Good First Issues (GFI) Tracker

> **$100 Prize Track** — Separate from hackathon project.
> **Strategy**: Find unassigned GFI+hackathon issues, claim on GitHub, fix quickly.

## Current GFI Status (April 19, 2026)

| Issue                                                                | Title                 | Assigned? | Difficulty | Area      | Action          |
| -------------------------------------------------------------------- | --------------------- | --------- | ---------- | --------- | --------------- |
| [#27444](https://github.com/open-metadata/OpenMetadata/issues/27444) | Start Here (welcome)  | N/A       | —          | —         | Read guidelines |
| [#27436](https://github.com/open-metadata/OpenMetadata/issues/27436) | Metrics docs link 404 | ✅ Yes    | Easy       | UI        | Taken — skip    |
| [#27419](https://github.com/open-metadata/OpenMetadata/issues/27419) | Trino lineage case    | ✅ Yes    | Medium     | Ingestion | Taken — skip    |
| [#25991](https://github.com/open-metadata/OpenMetadata/issues/25991) | Druid HTTPS           | ✅ Yes    | Medium     | Ingestion | Taken — skip    |

> ⚠️ Most existing GFI+hackathon issues are already claimed.

> 📌 **Apr 19, 2026 status update (verified via GitHub query)**: The only currently unassigned issue with both `good-first-issue` and `hackathon` labels is the welcome tracker [#27444](https://github.com/open-metadata/OpenMetadata/issues/27444) itself — which is informational, not actionable. The realistic GFI $100 path right now is to **ping @PubChimps on the OpenMetadata Slack** (per their note on #27444: _"Don't see a good-first-issue that is unassigned that fits your expertise? Please reach out to me on slack!"_) and ask for fresh GFIs to be created or routed. Daily polling of the [filter URL](https://github.com/open-metadata/OpenMetadata/issues?q=is%3Aopen+is%3Aissue+label%3Agood-first-issue+label%3Ahackathon+no%3Aassignee) remains worthwhile but is unlikely to yield results without proactive outreach.

## Strategy

1. **Daily check**: Run this query to find new ones:
   ```
   https://github.com/open-metadata/OpenMetadata/issues?q=is%3Aopen+is%3Aissue+label%3Agood-first-issue+label%3Ahackathon+no%3Aassignee
   ```
2. **Claim quickly**: Comment "I'd like to work on this" on the issue
3. **Types we can tackle**:
   - UI link fixes (OMH-BSE can handle these)
   - Documentation gaps in `openmetadata-mcp/`
   - Test coverage additions
4. **Before PR**: Read the [GFI guidelines in #27444](https://github.com/open-metadata/OpenMetadata/issues/27444)

## GFI Submission Rules (from #27444)

- ⭐ Star the repo
- Get assigned before submitting PR
- Check no existing open PR for the issue
- Build and test before submitting
- Include screen recording for UI fixes

## Owner: OMH-BSE (Bhavika)
