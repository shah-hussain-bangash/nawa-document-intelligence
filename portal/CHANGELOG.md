# v0.6.1 — Specific-field evidence grounding

- Missing supplier/contact/tax fields now abstain rather than cite price/name matches.
- Supplier binding, EN/AR labelled values, multiple-field/conflict checks and IBAN
  checksum; existing ACL/domain/version filtering; no model call on missing fields.
- Explicit UI unsupported/conflict labels and exact-version citation loading/polling.
- Audit status/reason metadata; actual package version in the sidebar.
- Guarded source-only updater with before-write hashes, source backup, unsafe-path
  refusal and rollback. No new dependency or DB migration. Broader quality gates remain.

# v0.6.0

- Bounded local English/Arabic scanned-PDF OCR, pinned language assets, layout text,
  word provenance, review warnings and needs_ocr retry; Docker includes executables.
- BM25 plus optional local dense embeddings/rank fusion, permission/classification
  filtering, bounded capacity and strict vector/route validation.
- Real HTTPS Keycloak verification and repeatable private synthetic fixture tools;
  issuer-origin/JWKS/authorised-party hardening and replay/logout/revocation checks.
- DB-backed document/workflow leases, bounded retries, stale-executor guards,
  creator revalidation and unique approval/run constraint (migration 7f0600000001).
- Verified offline SQLite+uploads bundles and new-directory restore; optional
  live-service, 100-case draft quality and local readiness probes.
- Browser scan/history/workflow checks, updated 26-phase status and honest measured
  quality gaps. Model-registry downloads were blocked; no production sign-off.

# All 26 phases — status at v0.5.0 (7 November 2026)

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
| 05 Identity | Local identities and OIDC adapter/tests | Keycloak chosen as optional free local IdP; live provisioning/MFA/recovery validation pending |
| 06 Isolation/audit | Application RBAC/ACL/CSRF, tenant tests, new composite FKs | RLS/full constraints, protected audit retention and access reviews |
| 07 Data/ground truth | Synthetic records and English/Arabic fixtures | Reviewed balanced 100-question held-out dataset |
| 08 Storage/lifecycle | Versioned local originals, hashes/pages, safe withdrawal | Governed object store, legal holds and tested retention/restore |
| 09 Parsing/OCR/tables | Bounded PDF/TXT extraction, page provenance, scan status | OCR/table adapters and representative bilingual accuracy tests |
| 10 Model gateway/budgets | Local extractive default, optional loopback Ollama and governed HTTPS adapter | Live endpoint, measured quality/cost and enforced tenant spending |
| 11 Hybrid retrieval | Permission-filtered lexical baseline | Approved embeddings, pgvector/hybrid and policy effective-date benchmark |
| 12 Grounded answers | Citations, source opening and abstention | Measured bilingual answer/citation quality and reviewed feedback |
| 13 Procurement/extraction | Labelled text drafts, persisted correction/review provenance and Decimal comparison | Arbitrary layouts/tables, units/charges/exclusions and extraction F1 |
| 14 Approval integrity | Revision-bound independent approval, replacement invalidation, pinned terminal reports | Broader concurrent/revoked-access/fault-injection acceptance |
| 15 Durable agents | Bounded graph and durable run records/replay | Distributed checkpoint/queue/retry/cancellation and tool reconciliation |
| 16 Bilingual/accessibility | Responsive navy/gold UI, keyboard dialogs, RTL/navigation/history labels | Complete Arabic copy/content review and accessibility audit |
| 17 HR/service | HR-scoped knowledge and persistent tickets | Domain validation, authorised connectors and SLA acceptance |
| 18 Forecasting | Synthetic time series, naive baseline/holdout error | Authorised dataset, registry/drift and temporal evaluation |
| 19 Evaluation/red team | 94 deterministic tests and browser journeys | Reviewed live-model metrics and independent assessment |
| 20 Reliability/observability | Readiness, lifecycle guards, backups, safe errors | Load/soak, SLOs, redacted telemetry/alerts and cost evidence |
| 21 Cloud/security | Local container/deployment reference files | Approved account/region, IAM/KMS, private network/storage and provisioning |
| 22 Staging/pipeline | CI/Compose/migration definitions | Actual immutable staged deployment and rollback verification |
| 23 Pilot/UAT | Reproducible local demonstration | Named participants, documented pilot acceptance and remediation |
| 24 Release/DR | Versioned archives, checksums and consistent SQLite pre-migration backup | Full DB+objects restore, rollback, revocations and measured RTO/RPO |
| 25 Operate/handover | Runbooks, limits, source manifest and troubleshooting | Assigned operators, incident exercises, patch/access cadence and handover |

## Dependencies needed to finish live phases

Select a cloud account and approved service-specific region, identity provider,
model/embedding/OCR routes, data classification/retention profile, spending limit,
review participants and operating owners. Credentials belong in local/managed
secret settings, not chat or source. Availability of a region is not evidence that
all processing, support, backups and telemetry meet residency requirements.

## Next code work

After validating this history release with the user, build and evaluate an OCR/
table adapter against reviewed English/Arabic samples, then introduce hybrid
retrieval against held-out questions. Expand checkpoints/queues where measured
workflow needs justify them. Security and tenant tests continue with each feature.
The original implementation guide retains all phase dependencies and broader gates.

The user selected free options: use the local default, optional Ollama and local
Keycloak configuration in 19_FREE_LOCAL_SERVICES.md. An approved paid cloud
account is not assumed; there is no permanently free hosted production claim.
