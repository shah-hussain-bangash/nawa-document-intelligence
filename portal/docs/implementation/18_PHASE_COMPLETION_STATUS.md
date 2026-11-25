# All 26 phases — status at v0.6.0 (7 November 2026)

This is a working complete-source local sandbox release. It is not a claim that
all 26 operational phases, AI quality targets or sovereignty requirements passed.
Reference PDFs are specifications, not completed verification evidence.

| Phase | Implemented baseline | Remaining acceptance gate |
|---|---|---|
| 00 Scope/ownership | Independent synthetic procurement scope documented | Named owners, budget/capacity and acceptance approval |
| 01 Workflow/UX | Case/evidence/quotation/reviewer journeys, designed UI | Representative user usability and policy validation |
| 02 Architecture/profile/threats | Modular design, boundaries, allowlisted model routes | Deployment-specific threat/residency/provider/legal review |
| 03 Tools/repository | Cursor setup, universal locks, process lifecycle and packaging | Fresh native Windows/macOS matrix and configured source CI |
| 04 Foundation/CI | Typed API/React, migrations, health, tests and CI definitions | Executed hosted CI/artifact/signature chain |
| 05 Identity | Local identities, hardened OIDC and seven real Keycloak code/PKCE/session checks | Real organisation provisioning, MFA/recovery, identity operations and deployed trust validation |
| 06 Isolation/audit | Application RBAC/ACL/CSRF, tenant tests, new composite FKs | RLS/full constraints, protected audit retention and access reviews |
| 07 Data/ground truth | Synthetic records and English/Arabic fixtures | 100 bilingual draft cases added; human-reviewed representative held-out data remains required |
| 08 Storage/lifecycle | Versioned local originals, hashes/pages, safe withdrawal | Governed object store, legal holds and tested retention/restore |
| 09 Parsing/OCR/tables | Bounded PDF/TXT extraction, layout text, real English/Arabic OCR, word boxes and warnings | Arbitrary structural tables and representative bilingual quality; Arabic fixture F1 is only 0.80 |
| 10 Model gateway/budgets | Local extractive default, optional loopback Ollama and governed HTTPS adapter | Live endpoint, measured quality/cost and enforced tenant spending |
| 11 Hybrid retrieval | Permission-filtered BM25, local dense embedding adapter and reciprocal-rank fusion | Live embedding quality, pgvector/distributed index, effective-date reasoning and reviewed benchmark |
| 12 Grounded answers | Citations, source opening and abstention | Measured bilingual answer/citation quality and reviewed feedback |
| 13 Procurement/extraction | Labelled text drafts, persisted correction/review provenance and Decimal comparison | Arbitrary layouts/tables, units/charges/exclusions and extraction F1 |
| 14 Approval integrity | Revision-bound independent approval, replacement invalidation, pinned terminal reports | Broader concurrent/revoked-access/fault-injection acceptance |
| 15 Durable agents | DB-backed polling, bounded ingestion retries, document/workflow leases, guarded replay and unique approval/run | Distributed graph checkpoints/queue, tool reconciliation and side-effecting agent fault acceptance |
| 16 Bilingual/accessibility | Responsive navy/gold UI, keyboard dialogs, RTL/navigation/history labels | Complete Arabic copy/content review and accessibility audit |
| 17 HR/service | HR-scoped knowledge and persistent tickets | Domain validation, authorised connectors and SLA acceptance |
| 18 Forecasting | Synthetic time series, naive baseline/holdout error | Authorised dataset, registry/drift and temporal evaluation |
| 19 Evaluation/red team | Automated security/integration tests, browser journeys, 100-case draft quality report and real local IdP checks | Reviewed live-model metrics and independent assessment |
| 20 Reliability/observability | Readiness, lifecycle guards, backups, safe errors | Small 100-request readiness probe passed; workflow load/soak, SLOs, telemetry/alerts and cost evidence remain |
| 21 Cloud/security | Local container/deployment reference files | Approved account/region, IAM/KMS, private network/storage and provisioning |
| 22 Staging/pipeline | CI/Compose/migration definitions | Actual immutable staged deployment and rollback verification |
| 23 Pilot/UAT | Reproducible local demonstration | Named participants, documented pilot acceptance and remediation |
| 24 Release/DR | Versioned archives, pre-migration DB backup and verified DB+original-file backup/restore bundles | Production PostgreSQL/object restore, rollback/revocations and measured RTO/RPO |
| 25 Operate/handover | Runbooks, limits, source manifest and troubleshooting | Assigned operators, incident exercises, patch/access cadence and handover |

## Dependencies needed to finish live phases

Select a cloud account and approved service-specific region, identity provider,
model/embedding/OCR routes, data classification/retention profile, spending limit,
review participants and operating owners. Credentials belong in local/managed
secret settings, not chat or source. Availability of a region is not evidence that
all processing, support, backups and telemetry meet residency requirements.

## Next code work

Validate the free local embedding/generation models after download, review the
100 draft cases, and measure representative bilingual OCR/table extraction and
retrieval/abstention. The measured BM25 Recall@4 of 0.50 and unsupported-question
abstention of 0.45 are open quality gaps, not passed acceptance targets. Continue
structural table handling, policy effective dates and production isolation/storage
work before widening real-data scope. Security and tenant tests continue per feature.
The original implementation guide retains all phase dependencies and broader gates.

The user selected free options: use the local default, optional Ollama and local
Keycloak configuration in 19_FREE_LOCAL_SERVICES.md. An approved paid cloud
account is not assumed; there is no permanently free hosted production claim.

## v0.6.0 evidence and limits

See `20_V060_OCR_HYBRID_AND_RECOVERY.md` and `verification/v060/`. Real local
Keycloak passed seven checks. English/Arabic image-only OCR and source downloads
passed real browser checks. The Ollama container started, but model-registry
access was denied by the environment network policy; generation and semantic
quality are still unverified. No named owners, real-user UAT, cloud deployment,
independent audit or production sovereignty approval has been fabricated.

## v0.6.1 targeted grounding update

Guide 21 records specific-field missing-evidence checks, labelled supplier binding,
conflict handling and pinned citation loading. This improves the reported bank-account
case; it does not close general answer-quality, identity, deployment or UAT gates.
