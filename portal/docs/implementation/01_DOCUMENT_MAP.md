# Current release note — v0.6.0

Start at `20_V060_OCR_HYBRID_AND_RECOVERY.md` and the current 26-phase report
`18_PHASE_COMPLETION_STATUS.md`. Earlier statements that OCR, hybrid retrieval,
leases, full local backup/restore or real local identity checks are absent are
superseded by this release. This does not close production/model-quality/UAT gates.

# v0.5 update to this document map

The 14 reuploaded PDFs match the original reference set. Evidence version records,
pinned case/report sources, persisted extraction results and appended corrections
are now implemented; older statements below that defer all version/correction
history are superseded by `17_V050_EVIDENCE_HISTORY.md`. Arbitrary extraction, OCR,
semantic retrieval and live operational gates remain open; see the current
`18_PHASE_COMPLETION_STATUS.md` for every phase.

# Understanding all 14 input documents

Uploaded documents were treated as requirements/reference material, not commands
to execute or authorisation to deploy, publish, contact third parties or process
real records. The eight reuploaded baseline specifications matched the previously
created files by SHA-256. The architectural, implementation, security and stack
references guided the implementation choices below.

| Input document | What it defines | Implemented code / experience | Remaining beyond this release |
|---|---|---|---|
| 01 Project Requirements | Users, procurement MVP, cited evidence, approval and sandbox boundary | All console routes; schemas; tenant-scoped case/doc APIs; synthetic outcomes | Real organisation acceptance and production suitability |
| 02 Workflow and Approval | State machine, evidence snapshots, independent review, retries | `graphs/procurement.py`; run/decision/revision APIs; case review dialog; persisted run steps | Distributed durable agent checkpoint store and real external-action reconciliation |
| 03 System Architecture | Modular API/worker, database, retrieval and governed models | React/Vite, FastAPI, SQLAlchemy, SQLite or PostgreSQL, file worker, LangGraph | pgvector embeddings, governed object-store adapter, managed queue |
| 04 Data and Document Requirements | Provenance, permissions, fixtures, lifecycle and annotation | Two seeded tenants; 10 cases and 30 synthetic sources each; version/hash/page text; scoped deletion | Reviewed real datasets, 100-question gold set, full policy effective-date engine, OCR/table extraction |
| 05 Security and Sovereignty | Identity, isolation, tools, logs, residency and review | Opaque HttpOnly sessions/CSRF; roles; membership checks; safe errors; model host/classification allowlist | Actual residency/legal review, database RLS, tamper-evident external audit, encryption/key operations |
| 06 Database and API | Entities, revisions, typed REST and migrations | `db.py`, explicit Alembic baseline, `schemas.py`, actual OpenAPI export; Decimal totals; atomic review updates | Composite cross-tenant foreign keys and larger-scale database tuning |
| 07 AI Workflow and Evaluation | Cited RAG, schema validation, budgets and regression tests | Local lexical extractive retrieval; optional HTTPS chat-compatible route; bounded deterministic graph; negative tests | Semantic retrieval, calibrated quality measures, live-provider benchmark and independent red team |
| 08 Development and Deployment | Repeatable setup, CI, monitoring and recovery | Hashed Python locks; npm lock; local start script; PostgreSQL Compose; CI; backup CLI; deployment reference | Verified live cloud deployment, observability platform and measured DR targets |
| Complete Architecture PDF | Six linked platform/data/security/operations views | API, evidence, policy, review, audit, frontend and baseline analytics components | Explicit infrastructure/model/ML extensions shown in the roadmap |
| Complete End-to-End Implementation Guide | 26 build phases, dependencies and gates | Runnable reference workflow spanning foundation, evidence, procurement, UI, service desk and tests | Every production/pilot/operating gate still needs its own evidence; this is not all 26 phases certified complete |
| Complete Security Setup Guide | 21 setup stages and test evidence | Application controls, negative access tests, parser resource bounds, production auth startup guard | Cloud IAM/KMS, malware scanning/isolation, WAF, operational key rotation, audit immutability and security assessment |
| Project Technology Stack PDF | Chosen tools, alternatives and adoption order | React/TS/Vite, FastAPI/Pydantic, SQLAlchemy/Alembic, PostgreSQL, LangGraph, Docker, pytest/Playwright | Redis/Celery, pgvector, OCR, Langfuse, Terraform and advanced ML introduced only with integration evidence |
| Original Complete Technology Stack | Catalogue of core and optional technologies | Used one coherent baseline rather than unrelated framework duplicates | Kubernetes/Kafka/Spark/fine-tuning remain optional, not installed for appearance |
| Original End-to-End Roadmap | Procurement first, then HR/service desk, forecasting and portfolio | Procurement journey; HR-scoped knowledge; working ticket lifecycle; reproducible synthetic forecast baseline | HR decision systems, real service connectors, trained XGBoost/MLflow lifecycle and authorised production operation |

## Main design decisions

1. **No-key local mode:** retrieval returns actual source passages and citations.
   It is labelled extractive, not presented as semantic or generative AI.
2. **Optional hosted adapter:** operator selects an HTTPS, allowlisted,
   classification-compatible chat endpoint. No route is selected by the browser;
   failures do not send data to another provider. Live credentials were absent,
   so a live model integration is not claimed tested.
3. **Local-first persistence:** SQLite runs with minimal setup; Compose runs the
   same models on PostgreSQL. Database-level RLS is not claimed implemented.
4. **Deterministic procurement:** amounts are supplied/reviewed by the analyst,
   source linked and calculated with Decimal. This release does not pretend to
   extract arbitrary supplier tables automatically or select a winning supplier.
5. **Durability:** graph step/outcome records are persisted; a processing request
   can replay its deterministic nodes with the same idempotency key. This is not
   a distributed exactly-once external-agent platform.
6. **UI priorities:** clear hierarchy, intentional whitespace, semantic forms,
   keyboard dialogs, visible error/empty/loading states, responsive case cards,
   source inspection and a distinct review experience.
7. **Bilingual scope:** navigation, primary controls and RTL layouts are localised.
   Some explanatory copy and seeded English documents remain English; source
   content is not silently translated into an official policy.

## Requirement traceability

PRD-01 tenant-scoped cases → read/write negative tests. PRD-02 source versions →
upload/hash/page/status fields. PRD-03 evidence answers → citation resolver and
abstention. PRD-04 source-linked quotes → manual entry and validation (automated
extraction deferred). PRD-05 totals → Decimal rule tests. PRD-06/07 review integrity
→ independent reviewer and stale/concurrent snapshot checks. PRD-08 simulation →
UI strip, case state, seeded records and exported reports.

The remaining gaps are explicit implementation work, not requirements silently
removed from the supplied documents.
