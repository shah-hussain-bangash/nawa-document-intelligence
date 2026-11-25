# v0.5.0 — Versioned evidence and saved correction history

## Delivered local end-to-end journey

Upload a PDF/TXT → process → extract labelled quotation fields → edit draft fields
beside their page passages → record review reason and confirmation → apply/save
case → compare → independent reviewer → simulated outcome → historical report.

New capabilities:

- Original source versions retain their file, hash, pages, actor and timestamp.
  New versions append a record and update the latest-document view. There is no
  API that edits a ready version's content in place.
- Extraction results are saved with exact source version, hash, field passages,
  extractor version, actor and time. Reviews append corrected values, before/after
  changes, reason and actor; the original extraction output stays unchanged.
- Quotation forms can edit fields in the review dialog. Applying saves a review
  record; case saving remains a separate action. Further manual edits clear the
  review link, distinguishing manual values from a saved reviewed draft.
- Server checks prevent a review ID being attached to changed values or a different
  source/version. Missing fields stay unknown until a person supplies them.
- Cases pin each source version. Replacement invalidates affected pending approvals
  and cancels their old run state; a fresh source review/comparison is required.
- Terminal cases retain their evidence pins. Their reports and source links resolve
  historical evidence, rather than silently substituting the latest document.
- Source viewer offers version selection, original downloads, new version upload
  and extraction/correction history with reviewer attribution.
- Composite foreign keys protect tenant boundaries on the new version/extraction
  entities. Existing application authorisation is still checked for every route.

## Run in Cursor

This is a complete-source release: frontend, backend AND database migration are
required. Do not mix its UI files with an older backend.

For an existing default SQLite/local-storage installation:

1. In the OLD workspace stop the application using Ctrl+C, or on Windows run
   `py -3.12 nawa.py stop`. Do not operate both versions against the same database.
2. Back up `.env`, `.data` and any customised source. Original uploads are in the
   data folder; a database-only backup is not a backup of those original files.
3. Extract the full v0.5 ZIP into a NEW folder; open its `nawa-workspace` in Cursor.
4. Copy the old `.env` and `.data` into that folder AFTER the old server stops.
   Do not copy `.venv` or node_modules. Preserve intentional absolute database/data
   locations; check those settings before migration. No secret values need posting.
5. Run:

```powershell
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

Or use `SETUP_AND_RUN_WINDOWS.cmd`. Wait for SETUP COMPLETE and READY. The setup
backs up an existing versioned SQLite database before applying a new migration.
The backup appears in a `backups` folder beside the database file. It contains
pre-upgrade records and uses restrictive file permissions where supported.
PostgreSQL deployments need their operator's database/storage backup procedure.

No reboot is part of the workflow. Read the retained v0.4.2 lifecycle guide if a
native Windows file is blocked by an unrecognised process or access policy.

## Try the new feature

1. Upload an included labelled quotation sample. In a New case select it as a
   quotation's source, then Extract from source.
2. Change a value in the draft table if needed. Supply a correction/review reason,
   confirm you reviewed the passages and apply. Create/save the case separately.
3. Open that document in Documents. Extraction history shows the original result
   and appended reviews with before/after corrections, reason, actor and time.
4. Upload a changed file through Add a new version. The old version remains in the
   selector. Affected nonterminal cases need refreshed evidence and comparison.
5. Select version 1 and download its original file. An already approved/rejected
   case continues to reference its own historical evidence version.

## Migration and retention contract

Migration 4283578082f1 follows 9abe5d076321. It adds document_versions, extractions,
extraction_reviews, a case evidence-version map and tenant constraints. It copies
existing document metadata/pages into version records and pins existing cases.
It preserves legacy file names/paths. It does not reconstruct revisions that were
never stored by earlier releases, or fabricate earlier extraction reviews.

“Immutable” here means append-only through normal application actions. It is not
WORM storage or a guarantee against database/storage administrators. Withdrawing a
source deliberately removes access, deletes original files and purges stored text,
extracted values and review text, while retaining minimal version/audit metadata.
It also prevents old download/history routes bypassing current source access.
Legal holds, external backup expiry and regulated retention remain operational
requirements requiring the selected profile.

## Verified and limitations

100 tests passed and one native Windows job test skipped in Linux. Checks include
old populated schema upgrade, readable consistent pre-upgrade backup, source file
preservation, review lineage, stale version/review rejection, approval invalidation,
terminal report pinning, foreign-tenant denial and composite DB constraints.
Migrations/schema check, TypeScript/production build and formatting passed.
Chromium exercised uploaded source, correction persistence, replacement version,
old pages/downloads and mobile history. Existing citations/upload/comparison/
independent review/PDF/mobile/Arabic journey passed as well. No native Windows
v0.5 execution, live IdP/model/cloud deployment or independent security audit is
claimed. One upstream LangChain deprecation warning remains non-fatal.

The repeated browser case title in the old runner could select a previous approved
case. The runner now generates unique titles for repeatable verification.

The 14 reuploaded PDFs match the reference set already reviewed. See
18_PHASE_COMPLETION_STATUS.md for what this package does and does not complete.
