# Synthetic review-aware comparison

This draft changes the authenticated synthetic PostgreSQL demo's comparison
only. It does not modify the stored source quotation. The unauthenticated
memory demo retains its existing behavior.

- An item with no review uses its original extracted values and existing
  financial checks; this is a synthetic preview, not an approval.
- An item with a pending, changes-requested or rejected review is displayed
  but excluded from ranking.
- An approved review is replayed and checked against its database revision,
  original quotation fields and source evidence. Comparison uses the reviewed
  fields and recalculated financial checks, and identifies the review revision.
- A malformed review, revision mismatch or original-source mismatch fails the
  comparison rather than silently returning an old value.

Source evidence in a comparison remains the original extraction evidence. The
default `legacy_asserted` correction policy preserves the existing behavior:
excerpts are reviewer assertions and are not independently verified.

The synthetic server can opt in at startup with
`NAWA_SYNTHETIC_CORRECTION_SOURCE=require_intake_txt`. In this mode a correction
requires a tenant-scoped intake promotion with retained UTF-8 TXT source; the
source file is read and checked against its recorded SHA-256, and the supplied
document name, line number and full excerpt must match the source. The same
check is repeated for prior correction events before approval and before using
approved corrected values in comparison. Missing, altered, cross-tenant,
unsupported PDF, or unretained sources fail closed. Existing records are not
backfilled or deleted. The isolated Phase 13 QA stack opts into the policy;
the default and running portal remain unchanged.

This check establishes only that a cited line matched the retained source at
the time of the check. It does not prove that the correction follows from that
line, verify worker identity, make file access atomic against a malicious
local writer, or establish a durable independent attestation. Hash-linked review
history is not an immutable or independently authenticated audit record.
The feature is synthetic-only and does not establish production financial,
tenant-isolation or procurement-approval controls.
