# Data Flow

> LLM in diagrams: **OpenAI GPT-4o-mini** via `langchain-openai` (see [CLAUDE.md](../../../CLAUDE.md)). HITL + governance store: [FeatureDev/GovernanceEngine.md](../FeatureDev/GovernanceEngine.md).

## End-to-end read path (search / details)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Chat_UI
    participant API as FastAPI
    participant A as LangGraph_Agent
    participant LLM as OpenAI_GPT4o_mini
    participant MCP as OM_MCP_Server
    participant OM as OpenMetadata

    U->>UI: NL message
    UI->>API: POST /api/v1/chat
    API->>A: run_chat_turn
    A->>LLM: intent + tool selection
    LLM-->>A: read tool proposal
    A->>MCP: search_metadata / get_entity_details
    MCP->>OM: REST / search
    OM-->>MCP: JSON
    MCP-->>A: structured result
    A->>LLM: format_response
    LLM-->>A: Markdown
    A-->>API: JSON + audit_log
    API-->>UI: 200
    UI-->>U: rendered Markdown
```

## Write path with HITL (auto-classify / patch_entity)

`POST /chat/confirm` is a **separate HTTP entry** (not a LangGraph node): it resolves pending state in `sessions`, transitions governance state, and enqueues service-layer OM write-back — see [AgentPipeline.md](./AgentPipeline.md).

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Chat_UI
    participant API as FastAPI
    participant Sess as SessionStore
    participant A as LangGraph_Agent
    participant LLM as OpenAI_GPT4o_mini
    participant GW as GovernanceWriteback
    participant MCP as OM_MCP
    participant GS as GovernanceStore

    U->>UI: classify request
    UI->>API: POST /api/v1/chat
    API->>A: run_chat_turn
    A->>GS: transition SCANNED / SUGGESTED
    A->>LLM: propose patch_entity
    LLM-->>A: ToolCallProposal
    A-->>API: 200 + pending_confirmation
    API-->>UI: show modal

    U->>UI: Confirm
    UI->>API: POST /api/v1/chat/confirm
    API->>Sess: resolve proposal_id + accepted=true
    Sess->>GS: transition APPROVED
    Sess->>GW: enqueue write-back (APPROVED)
    GW->>MCP: patch_entity async
    MCP-->>GW: success/failure logged
    API-->>UI: 200 + audit_log
```

## Drift detection and read API

```mermaid
sequenceDiagram
    participant Drift as DriftWorker
    participant MCP as OM_MCP
    participant GS as GovernanceStore
    participant API as FastAPI
    participant UI as Operator_UI

    loop Every N minutes
        Drift->>MCP: get_entity_lineage / get_entity_details
        MCP-->>Drift: live payload
        Drift->>GS: compare hash / tags, maybe DRIFT_DETECTED
    end

    UI->>API: GET /api/v1/governance/drift
    API->>GS: list DRIFT_DETECTED
    GS-->>API: entities + signals
    API-->>UI: JSON
```

## Auto-classification (conceptual loop)

Same as shipped design: scan → details per table → LLM classify → **HITL** → `patch_entity` (never skip confirmation for hard writes).

```mermaid
sequenceDiagram
    participant U as User
    participant A as LangGraph_Agent
    participant MCP as OM_MCP
    participant LLM as OpenAI_GPT4o_mini

    U->>A: Auto-classify customer_db
    A->>MCP: search_metadata
    MCP-->>A: tables

    loop Per table
        A->>MCP: get_entity_details
        MCP-->>A: columns
        A->>LLM: classify PII
        LLM-->>A: tag suggestions
    end

    A-->>U: pending_confirmation or summary
    Note over U,MCP: User confirms via POST /chat/confirm before patch_entity executes
```

## Drift Detection Flow

```mermaid
sequenceDiagram
    participant LP as Lifespan Poll Loop
    participant DS as Drift Service
    participant MCP as OM MCP
    participant OM as OpenMetadata
    participant API as GET /governance/drift
    participant U as User/Demo

    loop Every N seconds
        LP->>DS: run_drift_scan()
        DS->>MCP: search_metadata(query=*, limit=100)
        MCP->>OM: GET /api/v1/search/query
        OM-->>MCP: Search results
        MCP-->>DS: Entity list

        loop For each entity
            DS->>MCP: get_entity_details(fqn)
            MCP->>OM: GET /api/v1/tables/{id}
            OM-->>MCP: Entity details
            MCP-->>DS: Entity JSON
            DS->>DS: hash + tag compare vs baseline
        end

        DS-->>LP: DriftSnapshot (cached)
    end

    U->>API: GET /api/v1/governance/drift
    API->>DS: get_latest_snapshot()
    DS-->>API: DriftSnapshot
    API-->>U: JSON {drift, scanned_at, ...}
```
