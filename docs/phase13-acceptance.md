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
| End-to-end dashboard and identity | Backend and worker integration pass, and a real browser exercised the synthetic dashboard against stubbed authentication and API responses. A real-browser workflow against live Keycloak and PostgreSQL has not been verified. The user deferred the Phase 12 browser/certificate step. **Open.** |
| CI and review | At commit `0389baced611ce4b6e82ab5d4c6aae27e75c18c3`, GitHub Actions general tests reported 195 passed and 26 skipped; the separate Phase 13 PostgreSQL job passed 17 tests. Windows intake, synthetic Keycloak and Docker smoke jobs also passed. Check the latest runs on [Phase 13 draft PR](https://github.com/zenithdevelopers7-source/nawa-document-intelligence/pull/3), which remains unmerged. **Review and integration remain open.** |

## Remaining work before calling Phase 13 complete

1. Review the revalidation and failed-job retry controls. A read-only test-database inspector classifies known migration records, but cannot verify schema integrity or authorize an upgrade. Before upgrading any existing test database, verify its schema and migration history and make a separately verified backup. Intermediate draft histories that do not match the original `001` are intentionally rejected; do not reset existing data.
2. Complete a real-browser synthetic workflow after an approved certificate/hostname is available; do not bypass the browser warning.
3. Obtain an independent security review and address its findings, including tenant isolation, storage, parser safety and operational recovery.
4. Review the migration and dependency on Phase 12, then integrate only after the appropriate review and checks pass.

There is no reliable completion date until the external certificate and review availability are known. Work that does not depend on those inputs can continue in the isolated development copy.

