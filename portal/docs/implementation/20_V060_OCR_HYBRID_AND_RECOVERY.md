# v0.6.0 — OCR, hybrid retrieval, real identity verification and recovery

This release extends the runnable local project. It does **not** certify all 26
phases complete. The 14 reference PDFs remain specifications; implementation,
measured quality, deployment and business acceptance are different gates.

## Upgrade safely in Cursor

1. Stop the old launcher with Ctrl+C. On Windows `py -3.12 nawa.py stop` stops
   recognised processes from that exact project, including its document worker.
2. Back up `.env`, the database and original uploads, and any customised source.
   Do not run old and new servers against the same database. An absolute
   DATABASE_URL/DATA_DIR can still point to the old folder: inspect those settings.
3. Extract the entire v0.6.0 archive into a new folder. Open `nawa-workspace` in
   Cursor. Copy your old `.env` and `.data` only after stopping the old application.
   Do not copy node_modules or `.venv` from the old folder.
4. In the Cursor terminal, in the folder containing `nawa.py`:

```powershell
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

No Windows restart is required. Wait for SETUP COMPLETE and READY. A failed setup
does not grant a successful-start marker. Migration 7f0600000001 follows
4283578082f1. Existing versioned SQLite gets a consistent pre-migration DB backup;
that backup alone does not include uploads or replace a full data backup.
The new unique approval/run index intentionally rejects pre-existing duplicate
run approvals; investigate such records rather than deleting them automatically.

## Free local OCR

The parser retains embedded PDF layout text. Pages without embedded text can use
Poppler rendering and Tesseract with bundled, pinned Apache-2.0 English/Arabic
language data. See `data/ocr/provenance.json` and LICENSE. No document is sent to an
external OCR service. The normal image includes the executable dependencies.

Native Windows needs Tesseract and Poppler installed on PATH. Use the maintained
distributions linked by their official projects, and validate their provenance:
https://github.com/tesseract-ocr/tesseract and https://poppler.freedesktop.org/.
The Python setup deliberately does not install unverified system executables.
Alternatively, after normal setup creates your local database password, use:

```powershell
docker compose up -d --build
```

Open http://localhost:8080. This Compose deployment uses its own PostgreSQL and
evidence volumes; it does not automatically migrate your native SQLite records.
Do not run `down -v` if you want to retain those volumes. Docker licensing/resource
requirements depend on your use. No paid cloud resource is created.

Native local settings (also the defaults):

```dotenv
OCR_MODE=auto
OCR_LANGUAGES=eng+ara
OCR_MAX_PAGES=6
```

Limits: PDF/TXT ≤10 MB; PDF ≤60 pages; at most six scanned pages OCR per document;
rendered longest side ≤2400 pixels; bounded subprocess time and Linux resource
limits. Split longer scans into reviewed source documents. Mixed PDFs with an
unprocessed page stay needs_ocr, rather than silently ignoring a scanned page.
Blank pages can also require intervention; they are not automatically declared
irrelevant. The source viewer shows method/warnings and preserves the original.
Retry needs_ocr after installing tools or upload a text-based replacement.

OCR stores word boxes and confidence for review. It does not infer arbitrary
table semantics or certify field correctness. Tax/date misreads in the Arabic
fixture demonstrate why every quotation still requires a human source review.
Linux subprocess limits are not a malware sandbox; the separately tested Docker
execution had network disabled, read-only root, private temporary storage,
non-root UID and bounded memory/CPU/processes.

## Free hybrid BM25 + local dense retrieval

Default RETRIEVAL_MODE=lexical now uses BM25 with English/Arabic normalisation.
For real vector retrieval, run the optional local Ollama service:

```powershell
docker compose -f compose.free-services.yaml up -d
docker compose -f compose.free-services.yaml exec ollama ollama pull embeddinggemma:300m
```

Stop the native app and set the following in its local `.env`:

```dotenv
RETRIEVAL_MODE=hybrid
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_MODEL=embeddinggemma:300m
EMBEDDING_ALLOWED_CLASSIFICATIONS=synthetic
RETRIEVAL_MAX_CHUNKS=240
RETRIEVAL_MIN_COSINE=0.45
```

Review the model licence and its language/domain suitability. A model name is an
example, not a bilingual-quality guarantee. Generation remains independently
optional (MODEL_MODE=ollama); see guide 19. Native Python runs on the host:
loopback is not the Ollama container from inside another container.

Documents are permission/domain/status filtered before chunks are embedded.
Only configured classifications are sent to the local embedding endpoint;
other permitted sources remain eligible for the lexical leg. Vectors are
normalised and fused with BM25 through reciprocal rank fusion. Invalid dimensions,
NaN/zero vectors, redirects, unavailable services and excessive capacity fail
visibly. The corpus is bounded; there is no silent truncation or paid fallback.
No persistent cross-user vector cache can bypass withdrawal or ACL changes.

This is a small local on-demand hybrid implementation. It does not implement
pgvector, a distributed vector index, policy effective-date reasoning or a
measured semantic abstention policy. Production cannot use this loopback HTTP
embedding profile: it needs a separately approved deployment and transport.

## Live services and repeatable quality evidence

```powershell
py -3.12 nawa.py services
.\.venv\Scripts\python.exe -m scripts.evaluate_quality
```

`services` reports configured endpoint checks only. Unconfigured services say
not_configured, not passed. Missing OCR tools fail that check; ordinary text
development still works. The model probe checks one synthetic fact/citation;
it is not accuracy evaluation. No secret, token or provider response is reported.

`evals/knowledge-100.json` contains 50 English and 50 Arabic developer-authored
draft cases: 80 source-relevance questions and 20 unsupported questions. These
are not independently reviewed or held-out data. It includes cross-language
questions and unsupported legal/production questions to expose weak abstention.
Measured default BM25 Recall@4 = 0.50; unanswerable retrieval abstention = 0.45.
The two image-only fixture field F1 scores were English 1.00, Arabic 0.80.
These small fixture results are not representative real-document accuracy.
The reports deliberately retain failed cases; model and data quality gates remain
open. Rerun against the selected live model and reviewed representative data.

A real Keycloak 26.4.7 local HTTPS service passed code/PKCE login, signed ID token/
nonce, provisioned membership, state replay rejection, logout and revoked-user
rejection. `validate_identity_login.py` creates a disposable application database;
it never sends test logins to a production issuer. A reproducible fixture setup:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_local_identity.py --validation-realm
docker compose --env-file .data/local-identity/compose.env -f compose.local-identity.yaml -f compose.identity-validation.yaml up -d
.\.venv\Scripts\python.exe -m scripts.validate_identity_login --issuer https://localhost:8443/realms/nawa-validation --ca .data/local-identity/trust-bundle.pem --fixture .data/local-identity/fixture.json
```

Do not overwrite an existing identity directory. Use a separate copy/workspace
for this disposable validation realm. The test trusts the generated CA with TLS
verification enabled; credentials and tokens are never printed. Browser trust,
real organisation users, MFA/recovery and operator acceptance remain separate.
Discovery endpoints must use the configured issuer's HTTPS origin, and token
verification also checks the authorised party for multiple audiences.

Ollama's container started, but this cloud environment's outbound policy rejected
registry.ollama.ai model downloads. Model weights and actual semantic/generation
quality were **not** validated here. The source includes endpoint/quality checks
to run after downloading the model on your own computer; no proxy/TLS bypass
was used.

## Durable local recovery

The launcher starts API, frontend and document worker together. Document claims
have a five-minute lease and at most three automatic attempts. An interrupted
lease is reclaimed; an active lease is not stolen. Exhaustion stops at failed,
and an explicit retry starts a new attempt cycle. The worker rechecks creator
membership before persisting output. Version/token CAS prevents stale workers
publishing over a replacement or withdrawn source.

Deterministic procurement runs have renewable one-minute execution leases.
Interrupted runs can replay the same Idempotency-Key only after lease expiry;
completed requests remain idempotent. Every saved step checks lease ownership.
Final publication checks lease, evidence digest and case revision. Each run can
have at most one approval record at the DB layer. Failed runs are inspected and
restarted with a new key; no payment or external tool side effect is executed.
This is DB-backed polling/replay, not Redis/Celery or distributed LangGraph
checkpointing for side-effecting agents.

## Verified local backup/restore

Stop the app first. The launcher operation lock rejects backup while its own
launcher is running; separately started servers/workers must also be stopped.
Use a secure backup location outside `.data`:

```powershell
py -3.12 nawa.py backup "C:\UAE-AI-Backups\v060-before-change.zip"
py -3.12 nawa.py restore "C:\UAE-AI-Backups\v060-before-change.zip" "C:\UAE-AI-Restore\verified-data"
```

The bundle contains a consistent SQLite snapshot, original uploads and SHA-256/
size manifest. It excludes `.env`/identity keys. Restore validates paths, archive
limits, hashes and DB integrity, then atomically creates a NEW directory; it
never overwrites active data. The restored DB is `database.sqlite3`. Point a
separate local configuration at that DB and restored uploads, test roles/source
versions/reports, then make an explicit cutover. Keep your backed-up config
separately and review stale session/withdrawal obligations after any restore.
ZIP checksums are corruption detection, not encryption/authentication. Protect
backup storage and retention; use native coordinated backups for PostgreSQL.

## Final verification

123 automated tests passed and one native Windows job test was skipped in Linux.
Hash-locked setup, fresh migrations/schema drift, TypeScript/build/formatting,
local/production Compose syntax, real browser procurement/history/OCR journeys,
seven live local identity checks and the non-root offline OCR container passed.
A stopped-workspace backup/restore retained 76 versioned originals with matching
hashes and 29 synthetic cases. See `verification/v060/` for reports and limits.

## Remaining gates

Guide 18 enumerates all 26 phases. Real semantic/model quality, structural table
extraction, complete Arabic/accessibility review, governed cloud/RLS/object store,
protected audit retention, independent security, workflow load/soak, production
MFA/DR, representative pilot/UAT and operating ownership remain unaccepted.
Some need more code as well as deployment/business evidence. Passing local tests
or creating this source package does not close those gates.
