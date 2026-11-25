# UAE AI v0.2 — design and requirements review

The 14 PDFs reuploaded for this redesign match all 14 reference PDFs byte for byte.
They are specifications, not commands or proof of implementation. Existing source
was compared with their procurement, architecture, security, data and delivery
requirements. See `01_DOCUMENT_MAP.md` for each document's code mapping.

## This release

Original geometric falcon-inspired mark; UAE-inspired emerald, ivory and gold;
illustrative skyline; readable text; dark navigation; responsive task shortcuts;
linked dashboard metrics; keyboard skip link; reduced-motion support; English and
Arabic layout support. The logo is original project branding, not a national emblem.

Procurement adds own-case filtering, due/newest/budget sorting and rejected,
cancelled and failed state filters. Document browsing adds processing-state
filters. Case reports offer a printable HTML report for browser Save as PDF,
with escaped user content, source hashes/versions, quotations, exceptions and
review history. Server authorisation covers case and every attached source.
The report is a snapshot, not a signed certificate or automatic source verification.

`python nawa.py run --auto-ports` avoids occupied ports without killing processes.
The final URL is printed only after API and frontend readiness pass. Keep the
terminal running. Port selection has a small reservation-to-start race; startup
still checks availability and fails visibly if another application claims a port.

## All 26 implementation phases: current evidence and next gate

“Partial” identifies implemented pieces, not phase completion. Local reference
behaviour and templates do not complete live integration/operating gates.

| Phase | Current delivery | Remaining gate |
|---|---|---|
| 00 Scope/ownership | Synthetic procurement boundary documented | User owners, capacity, budget and acceptance sign-off |
| 01 Workflow/UX | Case, evidence, review and audit journey; redesigned console | User research, usability sessions and policy owner validation |
| 02 Architecture/sovereignty | Architecture, boundaries and model allowlist | Deployment-specific threat/residency/legal review |
| 03 Workstation/tools | Hashed universal locks, Cursor files, setup/run CLI | Native Windows 3.12/3.13 CI execution; user has run 3.12 locally |
| 04 Foundation/CI | FastAPI, React, migrations, health, test CI definition | Hosted CI execution and artifact retention |
| 05 Identity | Local synthetic identities; OIDC adapter and negative tests | Chosen live identity provider, provisioning, recovery and MFA |
| 06 Tenant/audit | Application checks, CSRF, scoped audit and role tests | Database RLS, composite constraints, protected audit retention |
| 07 Data/evaluation | Synthetic tenants/documents/cases, small smoke set | Reviewed 100-question balanced Arabic/English held-out gold set |
| 08 Upload/storage | Bounded upload, local originals, version/hash metadata | Governed object storage, lifecycle/holds, immutable multi-version model |
| 09 Parse/OCR/tables | PDF/TXT page extraction, isolated parser, needs-OCR state | OCR, table cells/coordinates and parser corpus evaluation |
| 10 Model gateway | Extractive default, optional governed HTTPS adapter | Live provider quality/cost validation and enforced tenant spending ledger |
| 11 Hybrid retrieval | Tenant/role-filtered lexical retrieval | Embeddings, pgvector, multilingual benchmark and effective-date policy engine |
| 12 Cited answers | Sources, citation opening, abstention and scoped queries | Full bilingual grounded generation evaluation and reviewed answer feedback |
| 13 Procurement/extraction | Typed analyst-entered quotes, source links, Decimal rules | Automated field extraction with reviewed corrections and evidence spans |
| 14 Review/state | Independent reviewer, revisions, stale/duplicate decisions | Extended concurrent/revocation/restart fault-injection suite |
| 15 Durable agents/tools | Bounded graph, persisted runs and deterministic replay | Durable distributed checkpoints/queue, scoped external tools/reconciliation |
| 16 Console/accessibility | Ten routes, responsive/RTL layouts, dialogs, reports | Full Arabic narrative/content review and independent accessibility audit |
| 17 HR/service | HR-scoped knowledge and persistent service tickets | Real service connectors, reviewed domain evaluation and operational SLAs |
| 18 Forecast | Synthetic workload, naive baseline and holdout error | Real authorised time-series data, time splits, model registry and drift |
| 19 Evaluation/red team | Deterministic workflow/security tests, browser journey | Independent security assessment and reviewed live-model metrics |
| 20 Reliability/operations | Readiness, bounded errors, backup utility | Load/soak tests, telemetry platform, latency/cost/SLO evidence |
| 21 Cloud/security | Deployment reference configuration | Approved cloud account/profile; IAM, KMS, private networking and provisioning |
| 22 Staging/pipeline | CI/Compose and migration references | Actual immutable staged deployment and rollback verification |
| 23 Pilot/UAT | Reproducible local demonstration | Authorised pilot, participants, acceptance evidence and operating review |
| 24 Release/DR | Versioned source package, checksums and local persistence | Isolated full restore, revocations, measured RTO/RPO and stabilisation |
| 25 Operate/handover | Setup, limits, document map and upgrade instructions | Named operators, patch/access review cadence, incident exercises and handover |

## Upgrade without replacing user data

1. Stop the old launcher with Ctrl+C.
2. Extract v0.2 into a NEW folder. Do not overwrite the running application.
3. Copy the old `.env` and `.data` into the new `nawa-workspace`, if using the
   default SQLite/local-file profile. Do not copy `.venv` or `node_modules`.
4. If DATABASE_URL or DATA_DIR uses an absolute path, preserve that path; do not
   replace an external database. Back up your existing data first.
5. In the new folder run `py -3.12 nawa.py setup`, then
   `py -3.12 nawa.py run --auto-ports`. Open the printed READY URL.
6. Confirm your cases/documents remain and try the new PDF report action.

This release does not claim all proposed phases complete, production sovereignty,
automated arbitrary quotation extraction, or measured AI quality thresholds.
