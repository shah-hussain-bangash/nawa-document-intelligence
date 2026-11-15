# Phase 8 — Human-in-the-loop quotation review (synthetic, local)

Adds an offline review ledger for quotation extraction results, with reviewer corrections, evidence references, explicit approval/rejection/request-changes decisions, optimistic expected-revision checks, a replayed financial-validation check, and SHA-256-linked event records. It does **not** integrate with a database, an authenticated application, or the existing RAG API; it is a separate demonstration layer.

## Run from the repository root

```bash
cd demo
python3 -m nawa_demo.review_cli init --quotation samples/english_quote.txt --ledger review_demo.json
python3 -m nawa_demo.review_cli show --ledger review_demo.json
python3 -m nawa_demo.review_cli decide --ledger review_demo.json --actor reviewer-1 --decision approve --reason 'Checked against the synthetic source' --expected-revision 1
python3 -m unittest discover -s tests -v
```

To try a correction instead of approval, initialize a **new** ledger file (the command intentionally refuses to overwrite existing files):

```bash
python3 -m nawa_demo.review_cli init --quotation samples/english_quote.txt --ledger review_correction_demo.json
python3 -m nawa_demo.review_cli correct --ledger review_correction_demo.json --actor reviewer-1 --field total --value 900.00 --reason 'Simulated mismatch correction' --source english_quote.txt --line 6 --quote 'Grand Total: 1050.00' --expected-revision 1
python3 -m nawa_demo.review_cli show --ledger review_correction_demo.json
```

That correction creates a **financial mismatch**; approval is then blocked until a further explicit correction restores consistency. The quote/reference is **a reviewer-provided assertion**, not authenticated proof of the underlying source. The correction's source filename must match the original document; the quoted text and line number are not verified against document bytes.

## Boundaries

- `--actor` is self-asserted. There is **no real authentication, role-based authorization, second-person approval enforcement, or reviewer separation of duties**. Never deploy this as an approvals API.
- JSON files provide local persistence only. `expected_revision` detects stale versions at the function level, but file writes have no multi-process locking and are not safe for concurrent reviewers.
- The hash chain detects naive accidental edits if the rest of the chain is left unchanged. It is **not tamper-proof**: anyone who can edit the JSON can recompute all hashes. No cryptographic signatures, immutable external log, retention policy, reliable timestamps, or secure audit service.
- Source evidence and PDF extraction accuracy are not independently authenticated; all tests are synthetic, and human review remains required.
- Numeric checks are strictly AED and VAT consistency. Approval is a synthetic review decision, not a real procurement award.
- The CLI intentionally never sends data to a model or network. Store ledger JSON outside public repositories when working with real data. Do not commit confidential records.

After running the demo, add these entries to the repository `.gitignore` before committing source changes:

```gitignore
demo/review_demo.json
demo/review_correction_demo.json
```

Keep the original `.gitignore`; do not overwrite it. The package intentionally adds **only new files** to your project.
