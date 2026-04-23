# Chat UI Feature Spec

## Owner: OMH-ATL (Aravind)
## Phase: 1 (scaffold) + 2 (connect) + 3 (polish)

---

## Overview

React-based chat interface styled to match OpenMetadata's design system. Connects to the FastAPI backend.

## Design Requirements

- **Color palette**: OM purple `#7147E8`, dark backgrounds, clean typography
- **Font**: Inter (same as OM UI)
- **Layout**: Left sidebar (optional) + main chat area
- **Responsive**: Mobile-friendly
- **Dark mode**: Default

## Components

| Component | Description |
|-----------|-------------|
| `ChatMessage` | Single message bubble (user or agent) |
| `ChatInput` | Text input with send button |
| `ResponseTable` | Render search results as tables |
| `LineageGraph` | Visual lineage tree (optional, use Mermaid) |
| `TagBadge` | Colored tag badges (PII, Tier, etc.) |
| `StatusIndicator` | Loading spinner, error state |

## API Integration

```typescript
// POST /api/v1/chat
const response = await fetch(`${VITE_API_URL}/api/v1/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: userInput, session_id })
});
const data = await response.json();
// data.response: string (markdown)
// data.session_id: string (persist for next turn)
// data.pending_confirmation?: object
```

## Phase Breakdown

| Phase | Tasks |
|-------|-------|
| Phase 1 | Scaffold with Vite, basic chat input/output, hardcoded responses |
| Phase 2 | Connect to FastAPI `/api/v1/chat`, persist `session_id`, render responses, show safe error-envelope messages |
| Phase 3 | OM-native styling, responsive, governance dashboard view |
