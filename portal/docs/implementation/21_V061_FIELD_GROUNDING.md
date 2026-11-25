# v0.6.1 — Evidence checks for specific fields

## Observed failure

The question “What is Falcon Digital's bank account number?” returned quotations
because BM25 matched the supplier name. Those quotations contained price/tax
numbers but no bank-account identifier. Relevant documents were incorrectly
presented without explaining that the requested field was unsupported.

## Changed behaviour

- Explicit questions about bank account numbers, IBAN, SWIFT/BIC, supplier email,
  phone and tax-registration numbers use a conservative labelled-field check.
- Supplier/account-holder identity must match; another supplier's details, a
  quotation total or a placeholder cannot satisfy the question.
- English/Arabic labels and Arabic digits are supported. IBAN includes a checksum
  check; other field checks validate supported shapes, not real-world legitimacy.
- All requested fields must be supported. Conflicting values are withheld; the
  assistant does not pick one. Unspecified/unrecognised identity needs clarification.
- Missing fields return insufficient_evidence, a clear English/Arabic message,
  and no unrelated quotations as supporting citations. The UI says Evidence
  unavailable or Conflicting evidence. Missing-field requests do not call an
  embedding or generation provider.
- Policy/process questions remain passage searches. A policy about how to verify
  bank details does not need to contain an actual bank account number.
- Existing tenant/role/domain/readiness checks apply before field inspection.
  Withdrawn and superseded current-source content cannot supply a live answer.
- Knowledge citations open the exact cited version. Source-viewer initial loads,
  manual selection and polling preserve the selected version; latest-source content
  is not flashed or substituted while a historical citation is opening.
- Audit records include answer status/reason/field names, not the question or field
  values. The footer now displays the actual package version instead of v0.4.

No new dependencies or database migration are introduced.

## Update an existing unmodified v0.6.0 installation

Use the small Knowledge Fix ZIP. It contains two items:

1. `apply_knowledge_fix_v061.py`
2. `knowledge_fix_v061/`

Stop the application with Ctrl+C in its running PowerShell terminal. Copy BOTH
items beside `nawa.py` in the existing project folder. Keep a separate backup of
your configuration/data/custom changes as usual. Then run:

```powershell
Set-Location "C:\UAE-Sovereign-Agentic-AI\nawa-workspace"
py -3.12 apply_knowledge_fix_v061.py
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py setup --stop-running
    if ($LASTEXITCODE -eq 0) {
        py -3.12 nawa.py run --auto-ports
    }
}
```

The updater validates every incoming hash and the expected v0.6.0 contents of
every source file it replaces BEFORE writing source. It refuses a running normal
launcher, unsafe/symlink paths, corrupted payloads and changed source files. The
old source is backed up under `.data/update-backups`. A failed file write rolls
back earlier writes. `.env`, database files and uploaded documents are not payload
targets. It does not automatically merge custom source or stop separately started
servers. Close those servers before updating.

If your source differs or the update is already present, review the message;
do not delete data to force it. Use the complete v0.6.1 source in a new folder and
follow the retained v0.6.0 upgrade guide, preserving intentional data paths. No
Windows restart or dependency-lock repair is required by this update.

After READY, reload the browser. The sidebar footer should show v0.6.1. Ask the
bank-account question again. With the supplied sample quotations and no approved
bank detail source, expect Evidence unavailable and no quotation citations.

## Supported source shape

This is an intentionally fictional test fixture, not payment information:

```text
SYNTHETIC TEST ONLY
Supplier: Example Services
Bank account number: 9911223344
Email: billing@example.invalid
```

Ask a specific question such as “What is Example Services' bank account number?”
or “What is the email address for Example Services?” Apostrophe/entity parsing is
limited; for an unambiguous supported form use “Bank account number for Example
Services?”. Identity may be labelled Supplier, Supplier name, Account holder or
Beneficiary, including supported Arabic equivalents. Each value needs a supported
label and colon. Arbitrary layouts, fuzzy aliases and cross-language name
translation are not inferred. Missing or conflicting details need an authorised
source and human review.

## Verification and scope

Final full checks: **162 passed, one native Windows job test skipped**; build,
formatting, setup, schema consistency and browser journeys passed. No broad
semantic-quality or production acceptance claim is made.


The reported failure, paraphrases, Arabic, positive supported fields, IBAN checksum,
multi-field requirements, conflicting values, other suppliers, missing identities,
role/tenant/domain filtering, version replacement and withdrawal have regression
tests. The source-only updater has tests for preservation, refusal, corrupted
payload, unsafe paths and rollback. Real browser checks cover the missing-field
warning/no false citations, supported fields, historical citation after replacement
and later polling, Arabic policy retrieval and the existing history workflow.

This is a targeted labelled-field safeguard, not a general semantic entailment
engine, complete abstention solution, authenticity/ownership check or production
certification. Free-form questions and model-generated claims still require broader
quality evaluation. Existing OCR/semantic-quality and all-phase production gates
remain open. See verification/v061 and guide 18.
