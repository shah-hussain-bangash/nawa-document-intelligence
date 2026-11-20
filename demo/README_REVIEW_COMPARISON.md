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

Source evidence in a comparison remains the original extraction evidence.
Correction excerpts in the review are reviewer assertions; this draft does not
independently validate them against original source bytes. Hash-linked review
history is not an immutable or independently authenticated audit record.
The feature is synthetic-only and does not establish production financial,
tenant-isolation or procurement-approval controls.
