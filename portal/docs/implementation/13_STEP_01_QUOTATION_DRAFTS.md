# Step 01 — Source-linked quotation drafts (v0.4.0)

## What this step delivers

Select a ready source in a case quotation form. Choose **Extract from source**.
The application reads explicit labels, presents six draft fields with source page
passages, document version/hash and extraction version, then requires a review
checkbox before **Apply reviewed draft**. Applying fills the form; creating or
saving the case remains a separate step. Comparisons and independent approval
are unchanged. Missing, invalid or conflicting values are blank for manual entry.
The extraction endpoint is audited. It does not approve or select a supplier.

English and Arabic label/digit handling are supported. No paid model key or new
dependency is needed. This is a conservative deterministic baseline, not arbitrary
quotation understanding, OCR, semantic retrieval or a measured field-F1 claim.

## Try it step by step

1. Sign in as Analyst in Emirates Operations.
2. In **Documents**, upload `data/sample/quotation-labelled-en.txt` and the Arabic
   sample beside it, using category Quotation and synthetic classification.
3. Wait until both documents show Ready. Open **New case** and enter title,
   department, budget, due date and requirements as usual.
4. Choose **Add two quotations**. Select the English document as the first source.
5. Click **Extract from source**. Verify each value and original page passage.
   Tick the review checkbox, then apply. Repeat with the Arabic source.
6. Correct any value manually if needed. Check validity dates against the date of
   your demonstration; the fixture expiry date is illustrative, not dynamic.
7. Create/save the case, run comparison, inspect amounts and exceptions, then
   sign in as an independent Reviewer to record a simulated decision.
8. Inspect the case report and audit history. No purchase or payment is executed.

## Supported input contract

One labelled field per line using `Label: value`. Recognised fields: Supplier /
اسم المورد, Net amount / المبلغ الصافي, Currency / العملة, Tax / الضريبة,
Delivery / مدة التسليم, Valid until / صالح حتى. Sample files show exact syntax.

- Net amount: positive decimal, max two decimal places, up to 100 million;
  optional AED/USD/EUR or named Arabic currency suffix.
- Commas accepted only as complete thousands grouping; Arabic digits/separators
  normalised for parsing. Original text retained in the displayed passage.
- Tax: explicit percent sign, range 0–100. No assumed 5% when absent.
- Delivery: explicit integer day count, 0–730. No assumed delivery time.
- Validity: ISO date YYYY-MM-DD. Ambiguous local date formats are not guessed.
- Repeated distinct or invalid candidates stay unresolved. Currency conflicts do
  not convert amounts. Incomplete drafts still require manual completion.

The endpoint rechecks session/CSRF, analyst/admin role, tenant, source ACL,
processing readiness and expected source version. It records only metadata in
audit, not raw source contents. Document instructions cannot execute tools: the
extractor is a fixed parser with no model, URL fetch or action path.

## Delivery limits

This step returns field provenance in the review response; it does not introduce
an immutable Extraction/Correction database entity or tamper-evident attestation
that a person read each passage. Existing case revision persistence records the
saved quotation values. Full correction lineage, immutable multiple source
versions and broader layout extraction are the next increments.

## Validation

`python nawa.py check`: 65 tests passed, fresh migration and schema consistency,
TypeScript/build and formatting passed. Fourteen new extraction cases cover
English/Arabic, unknown/conflicting values, invalid numeric formats, explicit
source provenance, untrusted instructions, authentication, CSRF, roles, tenant
and source ACLs, stale versions and unready documents.

Chromium checks exercised extraction, evidence passages, disabled apply until
review, populated form, nested-dialog close without accidental case submission,
mobile layout, and the existing upload/comparison/reviewer/report/RTL journey.
Verified in Linux. No native Windows execution or arbitrary-layout accuracy
benchmark is claimed. The existing upstream LangChain warning remains non-fatal.

## Upgrade from v0.3.x

This is a full functional release: the UI-only ZIP cannot add the backend route.
Stop the old application and back up `.env` and `.data`. Extract full v0.4 into a
new folder. For the default SQLite/local-file profile, copy `.env` and `.data`
into its `nawa-workspace`; preserve absolute external database/data settings.
Do not copy `.venv` or node_modules. In the new folder run:

```powershell
py -3.12 nawa.py setup
py -3.12 nawa.py run --auto-ports
```

Open the READY URL and keep PowerShell running. Existing records are not reset.
No new schema migration or dependency version was needed for this feature.
