# Phase 13: synthetic document ingestion design draft

Status: isolated synthetic prototype in progress. Phase 12 remains an open draft; browser sign-in and the security gate remain outstanding. The prototype is not deployed and is not suitable for production data.

## Current baseline

The original dashboard validates a filename and bounds the decoded upload to 4 MiB, then processes a temporary file. Its existing PostgreSQL mode stores extracted quotation data and reviews, but not original uploaded bytes. The separate Phase 13 development copy now contains experimental file storage, PostgreSQL job operations, an opt-in UI and a one-job worker. The schema remains a review draft and is not automatically applied.

## Proposed first milestone

The synthetic prototype stores sources under generated identifiers, tracks tenant-scoped metadata and SHA-256 digests, and verifies bytes before processing. The test database limits each tenant to 20 distinct documents and 16 MiB of registered source files; known quota rejections remove the just-created temporary source. An experimental PostgreSQL service links distinct stored sources into numbered version families with concurrency checks, and the opt-in draft UI can request and display version history. Storage is not enforced immutable. Never derive storage paths from user-supplied filenames.

Use a PostgreSQL job record with received, validated, processing, completed, failed and retry-pending states. Claim jobs atomically, bound retry attempts, record safe failure categories and recover expired worker claims. Define duplicate behavior per tenant and document version using database constraints; concurrent retries must not create duplicate results. Scope all document and job access using verified server-side tenant membership, including reads, retries and downloads. Design storage/database failure handling so interrupted writes do not appear as completed uploads.

Reject malformed, encrypted or unsupported PDFs according to an explicit policy. Enforce page, processing-time and resource limits; do not execute embedded content. Initial support should stay within the existing UTF-8 text and selectable-text PDF capabilities; OCR remains Phase 15. Specify storage permissions, retention, backup and restoration of both metadata and original bytes before presenting persistence as complete.

## Acceptance evidence

- Batch synthetic English and Arabic files, versioning, provenance and correct access control.
- Duplicate submissions and concurrent retry claims do not duplicate processing; another tenant cannot inspect or retrieve the source or job.
- Bad signatures, mismatched types, corrupt/encrypted PDFs, oversize files and unsafe filenames are rejected safely; malformed inputs do not expose secrets.
- Recover from worker restart, storage failure and bounded retries; verify checksums and restore both metadata and source bytes from a tested backup.
- Regression and integration tests run in CI, with the exact passing commit recorded. Performance and PDF security limits must be measured rather than assumed.

Before deployment, review the storage design and security boundaries against the final Phase 12 changes. The per-tenant registered-byte limit is not a filesystem quota or rate limit: temporary and orphaned files can remain after uncertain failures and need offline reconciliation. The worker supports an explicitly configured synthetic polling loop as well as one-shot execution; distributed operations and production supervision are not validated. On Linux, parser subprocesses have operating-system memory, CPU and output-file limits. On Windows, a job object applies a per-process memory limit and existing timeouts apply; there are no equivalent Windows CPU or file-size limits. These controls do not constitute a security sandbox. Browser sign-in and real-browser UI remain unverified, and the migration is for explicitly configured synthetic test databases only. No original workspace data, secrets or existing backups should be moved or overwritten.

