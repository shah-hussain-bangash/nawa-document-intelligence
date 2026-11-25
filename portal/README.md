# UAE Sovereign Agentic AI — v0.6.1

Independent bilingual evidence and procurement learning platform. Navy/gold React
console, FastAPI, versioned sources, reviewed quotation drafts, independent
simulated approval, local OCR, optional hybrid search and recovery workers.
No government affiliation or actual purchasing/payment execution.

## Latest knowledge fix

v0.6.1 adds supplier-bound checks for explicit bank/contact/tax identifier questions.
Missing fields produce **Evidence unavailable**, with no unrelated quotations as
supporting citations. Historical citation loading/polling also stays version-pinned.
See [the small updater and limits](docs/implementation/21_V061_FIELD_GROUNDING.md).
No new dependencies or database migration. The guarded updater preserves runtime
config/data and backs up source; changed local source requires review.

## Run in Cursor

Use Python 3.12 and Node.js 22.12+ or 24 LTS. Open the folder containing `nawa.py`:

```powershell
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

Open the READY URL and keep the terminal running. Ctrl+C stops API, frontend and
worker. No Windows restart or paid API key is required. Linux/macOS use python3.

**Upgrade:** stop the old application, back up configuration/database/uploads,
extract into a NEW folder and follow
[the v0.6.0 guide](docs/implementation/20_V060_OCR_HYBRID_AND_RECOVERY.md).
Copy `.env`/`.data`, not old node_modules/venv. Check absolute storage paths before
migrating; never run old and new versions against the same database.

## Included

- Responsive procurement, documents, knowledge, agents, service desk, analytics,
  security, audit and preferences; English/Arabic navigation and RTL.
- Tenant/role/CSRF boundaries, exact-subject OIDC, original source versions,
  extraction history, human corrections/reasons, evidence pins and historical reports.
- Decimal comparison, independent review, stale/duplicate guards and simulated outcomes.
- PDF/TXT parsing and local English/Arabic OCR with word boxes/review warnings.
  Native OCR needs Tesseract/Poppler; the built Docker image includes them.
- Default BM25; optional local dense embeddings with rank fusion and strict
  classification/capacity/route guards. No paid fallback or silent truncation.
- Document/workflow execution leases, bounded ingestion retries, crash recovery,
  guarded deterministic replay and a DB constraint preventing duplicate run approvals.
- Offline DB+original-file backup/verified restore, service probes, draft bilingual
  quality evaluation and local container/deployment references.

## Free local options and evidence

Default: SQLite/BM25/extractive answers, no model account. Optional free local
Ollama and Keycloak: [setup and limits](docs/implementation/19_FREE_LOCAL_SERVICES.md).
Seven real HTTPS Keycloak code/PKCE/token/session/revocation checks passed. OCR
passed on actual English/Arabic scans, including browser upload/view/download.
The container built and was tested separately from the native development setup.
Current v0.6.1 verification is in verification/v061; the retained v0.6.0 baseline had
123 automated tests pass and one native Windows job test skip.
Build/migration/browser reports are under
[verification/v060](docs/implementation/verification/v060/).

A 100-case developer-authored draft benchmark deliberately records weaknesses:
default BM25 Recall@4 0.50, unsupported-question abstention 0.45; image-only fixture
field F1 English 1.00 / Arabic 0.80. These are not reviewed held-out metrics. Real
model downloads were blocked by this cloud's network policy; generation and
semantic quality were not validated. Run `py -3.12 nawa.py services` and the quality
script on your PC after installing optional tools/models.

## All 26 phases are not production-accepted

Some remaining items need more code: arbitrary structural tables, effective-date
policy reasoning, production RLS/object storage, distributed checkpoints/tool
reconciliation, telemetry and full Arabic copy. Others need real deployment and
people: representative model/quality review, independent security/accessibility,
MFA/recovery, workflow load/soak, pilot/UAT, production DR and operating owners.
See the [26-phase status](docs/implementation/18_PHASE_COMPLETION_STATUS.md).
No cloud resources or billing are provisioned by this release.

The 14 specifications remain under docs/reference. SOURCE_MANIFEST.md lists source
files in reading order. Runtime data, secrets, environments and node_modules are
excluded from the ZIP. Bundled Tesseract data retains its licence and revision/hash
provenance in data/ocr. Synthetic OCR PDFs are in data/samples; quotation learning
samples from earlier releases remain available under data/sample.
