# Synthetic correction and approval separation

The protected synthetic review path records the server-derived issuer-and-subject identity hash of the person who starts a new review. It rejects approval by that identity or by an identity that made any correction in that review, even if the identity later receives the Reviewer role. A browser-supplied actor is not trusted. A different provisioned Reviewer can approve after the existing authorization, source, revision and financial checks pass.

This is a narrow synthetic safeguard, not proof of separation between people. One person may hold different accounts or identities. Historical correction actors from other systems might not be comparable. The approval check does not identify the uploader if another identity starts the review. Existing reviews without a recorded preparer remain replayable and use the earlier correction-author check; their review starters cannot be inferred. Existing reviews are not changed or migrated. An organization needs a trusted identity and provenance model, policy for historic records, and independent review before claiming complete separation of duties.

## Experimental submitter recording

In the explicitly gated disposable CI evidence stack, synthetic intake records a server-derived identity hash for every account that submits a source, including a duplicate submission. It does so in the same database transaction as registration. This is an experiment: the records are not yet used to deny approval, do not cover direct quotation upload, and do not prove that accounts represent different people. Old documents have no inferred submitter; absence of a row means unknown, not independent. The database itself can be altered by privileged users and the hashes are pseudonymous, not anonymous.

This adds an explicitly applied synthetic intake migration; it does not apply a migration to an existing installation or authorize a data upgrade. A previous synthetic schema will fail the new migration verification until explicitly updated. Migration, recovery, retention, policy for missing history and concurrent approval must be reviewed before using these records as an approval control.
