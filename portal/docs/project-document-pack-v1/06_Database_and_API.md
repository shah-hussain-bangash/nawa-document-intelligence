# Database and API Specification

Entity model, endpoint contracts and integrity rules

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. Data modelling principles

Use UUID resource identifiers, UTC timestamps, explicit tenant associations and versioned records. Financial fields use decimal types and currency codes. Keep immutable document versions separate from their logical document. Migrations are versioned and tested.
Use composite tenant/resource constraints where practical to prevent cross-tenant references. Business authorisation still applies above database constraints. Never treat a guessed UUID as an access mechanism.

## 2. Core entity groups

Identity: Tenant, User, Membership, Role and Permission. Evidence: Document, DocumentVersion, DocumentACL, Chunk and Extraction. Procurement: Supplier, Case, CaseRevision, Submission, EvidenceReference and ChecklistVersion.
Execution: WorkflowRun, Checkpoint, ToolInvocation, Approval and AuditEvent. Quality: Feedback, EvaluationDataset and EvaluationRun. Optional forecast entities are added only when that module exists.

## 3. Relationships and constraints

Tenant has many memberships, documents and cases. Document has many versions; chunks reference one immutable version. Supplier submissions link a case revision to permitted document versions. Approval references exactly one review snapshot.
CaseRevision has an incrementing revision number and explicit state. Approval stores reviewer, decision, reason, expected revision and action digest. Audit events record actor/action/resource without embedding unnecessary document content. Index tenant plus common state/date filters; benchmark vector indexes on the actual corpus.

## 4. API surface

GET /health/live: process liveness; GET /health/ready: dependency readiness. POST /api/v1/documents: multipart upload and asynchronous processing record. GET /api/v1/documents/{id}: scoped metadata/status. POST /api/v1/knowledge/query: question, permitted filters and an answer with citations or abstention.
POST /api/v1/cases: create case. GET /api/v1/cases/{id}: scoped case and revision. POST /api/v1/cases/{id}/runs: start workflow. POST /api/v1/approvals/{id}/decisions: approve/reject/request changes. GET /api/v1/audit: permission-controlled, paginated history.

## 5. Representative schemas

CaseCreate: title, purpose, checklist_version_id, applicable_date and supplier_ids. Server assigns id, tenant_id, revision, state and timestamps. DecisionCreate: decision enum, reason and expected_revision; server derives actor and revalidates the approval digest.
KnowledgeResult: status(answered/insufficient_evidence), answer, citations[] and correlation_id. Each citation includes document_id, version_id, page/section and evidence span reference. UploadResult: document_id, version_id and processing_state. Do not include storage credentials in responses.

## 6. HTTP and error conventions

Use 201 for created synchronous resources, 202 for accepted jobs, 401 for missing/invalid identity, 403 for denied actions, 409 for stale revision/idempotency conflict, 413 for size limits, 422 for invalid input, 429 for rate limits and 503 for unavailable dependencies. Apply a consistent 404 policy when resource existence is sensitive.
Error envelope: error.code, safe message, field details where appropriate and correlation_id. Never expose stack traces or private identifiers. Use cursor pagination and maximum page sizes; validate filter scope server-side.

## 7. Concurrency and idempotency

Run and decision endpoints accept an idempotency key scoped by tenant, actor and operation. Persist the request hash and response/outcome. Reusing a key with different input returns conflict. Define key retention in the operational profile.
Use optimistic concurrency for case revisions. Commit state transition, approval and business audit atomically where possible. Deliver background work with an outbox or equivalent durable design. Model requests execute outside database transactions; uncertain tool outcomes require reconciliation.

## 8. Schema lifecycle and access

Run Alembic migrations against a disposable database in CI, then test application compatibility. Prefer expand/migrate/contract changes. Back up before risky changes and verify the recovery strategy. Avoid deleting previous evidence versions as a schema-cleanup shortcut.
Enforce tenant/resource scope in repositories and workers. Document row-policy assumptions, bypass roles and connection-pool reset behaviour. Keep original storage references internal; issue short-lived download access only after permission checks.

## 9. Contract acceptance

Test create/read persistence, missing references, invalid decimals, cross-tenant references, stale decisions, concurrent transitions, duplicate requests, error envelopes and pagination. Verify that generated OpenAPI contracts and frontend types match implementation.
The implementation must supply exact field bounds, file limits, pagination defaults and index choices. These remain configuration/design decisions rather than invented production values in this baseline specification.
