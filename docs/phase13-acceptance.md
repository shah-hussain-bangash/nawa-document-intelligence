# Phase 13 acceptance checkpoint

Status: **prototype in progress; not production accepted**. This checkpoint assesses the Phase 13 ingestion criteria in the supplied office implementation playbook against the current draft. The draft PR is based on the unmerged Phase 12 draft.

| Playbook criterion | Evidence and status |
| --- | --- |
| Batch synthetic intake, allowed types and size limits | Automated HTTP, unit and synthetic UI tests cover TXT/PDF batches, per-file validation and quotas. **Prototype verified.** |
| File signature, safe names and duplicate behavior | Automated checks cover filenames, PDF signatures, digests and concurrent tenant-scoped duplicate submissions. A hash allowlist has a narrowly scoped exception for exact bundled synthetic PDF fixture variants. **Prototype verified; hostile-file assessment remains open.** |
| Durable source and metadata | Synthetic files use a named QA volume and PostgreSQL metadata; automated application/database restart and quiesced backup/restore checks include source hash and an approved review. **Prototype verified; no production storage or retention approval.** |
| Processing states and retry/dead-letter handling | The prototype validates before registration and stores `validated`; workers claim validated jobs, not unvalidated `received` records. It also supports `processing`, `retry-pending`, `completed` and `failed`; leases, retry bounds and recovery have automated checks. A permitted analyst can explicitly revalidate a `received` record or retry a failed record with a reason; the source is checked again and an event is recorded in the same transaction. A test upgrades the exact original `001` synthetic schema using `002` without losing source files or an approved review. The event log is not tamper-proof; other intermediate draft migration histories are not automatically upgraded. **Prototype verified; operations review remains open.** |
| Provenance and versions | Text and selectable-text PDF extraction attach line evidence; tested PDF evidence includes a page reference. PostgreSQL tests cover version history and concurrent updates. **Prototype verified for the tested fixtures; Arabic PDF layout and general extraction accuracy are not established.** |
| PDF safety and resource bounds | Synthetic tests cover malformed, encrypted, oversized and image-only inputs, timeouts, and platform-specific process resource limits. These are not a complete PDF security scan or sandbox. **Partial; independent security review remains open.** |
| Tenant and role boundaries | Automated local Keycloak tests use separate tenant-bound applications and verify denied cross-tenant reads, role checks and CSRF. **Prototype verified; no database row-level security and no independent review.** |
| End-to-end dashboard and identity | GitHub CI ran a real browser against the live synthetic dashboard, intake worker and PostgreSQL through start of review. A separate automated client obtained a synthetic Keycloak session and injected it into the browser; the browser did not perform the Keycloak sign-in. Windows CI also exercises the dashboard with stubbed responses. **Partial: actual browser sign-in and approved certificate remain open.** |
| CI and review | GitHub Actions passed on commit `0c95a027b52f6476d2ac103c2181485b38558b71`, including Windows intake, PostgreSQL integration, synthetic Keycloak, live-backend browser and Docker smoke jobs. Check the latest runs on [Phase 13 draft PR](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/3), which remains unmerged. **Review and integration remain open.** |

## Remaining work before calling Phase 13 complete

1. Obtain operational and independent security review of the revalidation and failed-job retry controls; repeated manual retries have no independent rate limit and events are not tamper-proof. A read-only test-database inspector classifies known migration records, but cannot verify schema integrity or authorize an upgrade. Before upgrading any existing test database, verify its schema and migration history and make a separately verified backup. Intermediate draft histories that do not match the original `001` are intentionally rejected; do not reset existing data.
2. Complete actual browser-based Keycloak sign-in and the synthetic workflow after an approved certificate/hostname is available; do not bypass the browser warning.
3. Obtain an independent security review and address its findings, including tenant isolation, storage, parser safety and operational recovery.
4. Review the migration and dependency on Phase 12, then integrate only after the appropriate review and checks pass.

There is no reliable completion date until the external certificate and review availability are known. Work that does not depend on those inputs can continue in the isolated development copy.

