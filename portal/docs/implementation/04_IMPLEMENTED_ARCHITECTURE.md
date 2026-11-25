# Architecture implemented by this source release

The earlier six-view PDF describes the full target. This diagram shows the actual
runnable reference, with external integrations explicitly distinguished.

```mermaid
flowchart TB
    Browser[React / TypeScript console\n10 routes, Arabic controls / RTL]
    Browser --> Proxy[Nginx production build OR Vite development proxy]
    Proxy --> API[FastAPI\nSafe errors, request IDs, limits, Origin checks]
    API --> Auth[Opaque sessions + CSRF\nCurrent membership + role / resource policy]
    Demo[Local synthetic demo identities] --> Auth
    OIDC[Optional OIDC BFF\nstate / PKCE / nonce / verified token] -.-> Auth
    Auth --> Cases[Case revisions + manual source-linked quotations]
    Cases --> Graph[Bounded LangGraph\nintake / Decimal checks / comparison]
    Graph --> Review[Version-bound independent human review]
    Review --> Outcome[Simulated outcome + audit event]
    Auth --> Knowledge[Scoped lexical evidence retrieval\nOriginal passages + page citations]
    Knowledge --> Gateway[Local extractive default\nOptional approved hosted chat route]
    Auth --> Upload[PDF / TXT upload\nPrivate generated file keys]
    Upload --> Worker[Durable document status + background ingestion\nIsolated parser process with Linux resource bounds]
    Worker --> DB[(SQLite locally OR PostgreSQL in Compose)]
    Worker --> Files[(Private local evidence directory / volume)]
    Knowledge --> DB
    Cases --> DB
    Review --> DB
    Auth --> DB
    Auth --> Tickets[Service desk lifecycle + HR knowledge space]
    Tickets --> DB
    Auth --> Forecast[Synthetic workload baseline\nTemporal hold-out MAE; advisory only]
```

Jobs claim queued documents atomically. Parser results cannot overwrite a deleted
document; stale review snapshots cannot produce approval. Graph steps/results are
stored in the application database. Deterministic graph replay is not claimed as
distributed exactly-once orchestration. The app has no real purchasing effects.

Core source boundaries: `core/` configuration/security/migration; `db.py` models;
`domain/` request schemas; `rag/` parser and retrieval; `graphs/` comparison;
`api/` authenticated routes; `ml/` baseline; `worker.py` ingestion; frontend
`ui.tsx` primitives, `pages.tsx` console routes and `workflows.tsx` business dialogs.
