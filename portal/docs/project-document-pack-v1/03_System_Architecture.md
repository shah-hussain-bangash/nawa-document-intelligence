# System Architecture Document

Components, boundaries and deployment choices

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. Architectural approach

Begin with a modular application: a React/TypeScript console, FastAPI service, background ingestion worker, PostgreSQL/pgvector database and object storage. Add a persisted LangGraph workflow for multi-step agent execution. Avoid independent microservices until operational evidence justifies them.
Logical request path: browser → API → verified identity and authorisation → case/retrieval/workflow service → scoped database/storage/model tools. All data paths carry verified tenant and resource scope.

## 2. Component responsibilities

Web console: case forms, evidence inspection, bilingual navigation and review queue. API: typed contracts, membership checks, rate limits and consistent errors. Case service: revisions, lifecycle and approvals. Ingestion worker: bounded parsing, provenance, chunking and indexing.
Retrieval service: authorised lexical/vector candidates and citations. Model gateway: provider policy, schemas, budgets and redacted usage records. Workflow runtime: checkpoints, retries and review interruption. Audit service: business evidence independent from debug logs.

## 3. Technology decisions

Baseline: Python 3.12+, FastAPI/Pydantic, SQLAlchemy/Alembic, PostgreSQL/pgvector, React/TypeScript/Vite and Docker Compose. Choose supported exact versions and commit lockfiles during implementation. Use one identity provider and one initial model integration.
Introduce Redis/Celery or a managed queue when ingestion requires asynchronous work. Use PostgreSQL text search as a lexical baseline and benchmark multilingual tokenisation before adding a dedicated search service. MCP is optional for a justified external tool integration.

## 4. Data and ingestion flow

Upload authorisation → size/type checks → quarantine or rejected state → object version storage → queued parse → text/table extraction → provenance validation → chunking → approved embedding endpoint → tenant-scoped index → ready state. Jobs are idempotent by document version and pipeline version.
Do not expose a partially indexed file as ready. Track failures and allow authorised reprocessing. Preserve original text; normalised search text must link back to original page and evidence locations.

## 5. Query and workflow flow

A query resolves verified identity, membership, document ACLs, effective policy date and classification. Retrieve permitted candidates, optionally rerank, then generate a schema-valid answer with resolvable citations or abstain. Filter permission before model context construction.
A procurement run reads a case revision, retrieves evidence, extracts typed fields, executes deterministic checks and generates a review draft. Persist an approval snapshot and pause. On reviewer decision, validate the same revision and permission before recording a simulated result.

## 6. Trust boundaries and consistency

Separate browser claims from verified identity, uploads from trusted instructions, model proposals from executable actions and business audit from operational traces. Signed storage URLs are short-lived and issued after authorisation.
Use database transactions for state updates; do not hold them across model calls. Use optimistic concurrency for revisions, an outbox where needed for durable job delivery and scoped worker identities. Test row-policy behaviour under pooled connections and privileged database roles.

## 7. Deployment profiles

Local sandbox: Compose with synthetic data, local database and object storage plus an explicitly permitted model endpoint. Cloud sandbox: private database/storage, TLS ingress, managed secrets and an approved inference route. Restricted profile: approved private inference, controlled imports and constrained telemetry/egress.
AWS is a candidate deployment platform, not a completed choice or evidence of sovereignty. Verify service-specific region support, processing terms and backup/support locations before committing to a profile.

## 8. Observability and failure handling

Propagate request/run correlation IDs. Record ingestion duration, retrieval and model latency, token/cost usage, retry rate, review wait and case outcome. Redact document content and personal information by default. Self-host tracing if the data profile requires it.
Use dependency readiness checks, bounded timeouts and explicit degraded states. Never route restricted data to an unapproved model as an outage fallback. Exercise queue loss, provider timeouts, invalid outputs and database recovery.

## 9. Evolution and architecture records

Capture decisions for tenancy, identity, model routing, storage, queue, retrieval and deployment. Each record states context, options, choice, consequences and a revisit trigger. Add Kubernetes, extra vector stores or streaming only after measured scaling requirements.
Architecture acceptance: a fresh environment starts reproducibly; one case flows across all intended components; permission boundaries are tested; dependency failures are visible; restore and rollback evidence exists before a deployment is described as operationally ready.
