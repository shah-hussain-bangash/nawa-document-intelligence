# Synthetic intake upgrade and recovery rehearsal

The proposed intake code requires migrations 008 and 009 even when tracked-submitter enforcement is off. An existing database at migration 007 fails startup verification until explicitly upgraded. This document is a review plan for disposable synthetic data, not authorization to upgrade or recover an existing service.

## Rehearsal gate

The integration test `test_007_backup_restores_then_upgrades_without_changing_original` creates uniquely named databases on the explicitly configured localhost QA cluster. It builds the schema through 007, records a synthetic source and review, takes a database dump and a separate file copy, and restores the dump into two isolated databases. It upgrades one copy to 009; it checks the original checksums, source bytes, job and review. The untouched original and the second restore remain at 007 and retain the review. The test drops only the three databases it created. It does not validate an actual user backup, object storage, live writers or identity-provider recovery.

## Before considering any real installation

1. Inventory the exact application and worker versions, the database and retained-source location, all writers, current grants, sessions and migration checksums. Review unknown or modified histories; do not bypass the verifier.
2. Agree a maintenance window and a coordinator that can stop and verify **all** writers and identity/session processes. Capture database and retained-file backups at the same quiesced point; protect and separately verify them.
3. Restore both backups into an isolated environment. Confirm the restored application can read representative approved reviews and source hashes, record migration history, and run the intended migration there. Verify both bilingual workflows, user roles and error handling. Do not infer historical submitter tracking or backfill it from absent evidence.
4. Rehearse rollback by restoring the pre-upgrade database and matching file snapshot into another isolated environment with the compatible old application version. Do not reverse the migrations manually. Document data-loss boundaries and decide how post-backup writes would be reconciled.
5. Review authorization, active grants, session invalidation, worker ownership and recovery coordination before resuming. The current synthetic guard is point-in-time only; stale restores can revive grants or sessions, and coordinated multi-process recovery is not established.

No production rollout, restore, migration or change to the running NAWA portal is approved by this rehearsal. The strict tracked-submitter experiment remains CI-only and cannot establish separation between people who hold multiple accounts.
