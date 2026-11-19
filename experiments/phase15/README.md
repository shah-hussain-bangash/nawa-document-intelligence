# Phase 15 synthetic OCR baseline

Status: **initial experiment; Phase 15 is not complete**. This tests two
local synthetic images and does not alter the running NAWA portal. No actual
procurement records are used.

## Local measurement

On 18 November 2026, Tesseract 5.4.0 was run once at page segmentation mode
6 using the official `tessdata_fast` English and Arabic models. The English
image was rendered from NAWA's bundled synthetic scanned PDF. The
Arabic-label image was rasterized from a locally generated synthetic PDF;
it is not a scan from a physical document. Both were rendered at 200 DPI.

| Synthetic case | Character error rate | Word error rate | Exact fields matched |
| --- | ---: | ---: | ---: |
| English, `eng` | 0.0% | 0.0% | 6 / 6 |
| Arabic labels, `ara+eng` | 46.4% | 53.8% | 2 / 6 |

For the Arabic sample, supplier and currency matched; subtotal, VAT rate,
VAT amount and total did not. Both cases are marked for human review. The
Arabic result must not be used to approve a quotation or assert the total.
The single English result does not establish general English OCR accuracy.

CER and WER use edit distance after NFKC normalization, removal of Unicode
formatting marks and whitespace collapse. They do not correct word order or
convert digits. Field checks require an exact recognized label and one value,
with Arabic digits converted for numeric comparison. The simple expected
transcriptions were authored alongside the fixtures, not independently
reviewed. `baseline-result.json` contains the synthetic output, individual
field checks and timing. The Arabic reference includes a title and footer;
missing them contributes to error rates.

The experimental field comparison now accepts comma grouping in numeric
values only when groups are well formed (for example, `1,050.00`); malformed
grouping is rejected and supplier punctuation is retained. Rechecking the
stored synthetic output with this rule did not change any of the five prior
case-level field results. This change does not improve the OCR output itself.

## Exploratory Arabic settings comparison

On the same synthetic Arabic-label image, 24 combinations of scale (original
and 2x enlargement), language order and Tesseract page segmentation were
compared. The best character error rate was 38.7%, using 2x enlargement,
`ara+eng` (or `eng+ara`), and segmentation mode 3 or 4. It still matched
only 2 of 6 fields, the same count as the original baseline. This is tuning
and measurement on the same single image, not independent validation or a
recommended production configuration. Numeric fields remain unreliable and
human review is required.

`arabic_variants.py` and `arabic-variants-result.json` record the local
experiment. Running it requires Pillow and the local files described below.
It refuses to overwrite an existing result; the enlarged image is temporary.

## Additional synthetic PDF pages

Three more pages were rasterized at 200 DPI and measured with the original
mode 6 settings. These are generated PDF pages, not physical scans; the
references are not independently reviewed, and the Arabic page shares content
with the earlier synthetic quotation. They do not establish general accuracy.

| Synthetic PDF page | Exact fields matched | CER | WER |
| --- | ---: | ---: | ---: |
| English, incorrect VAT example | 6 / 6 | 0.0% | 0.0% |
| English, second-page quotation | 6 / 6 | 0.0% | 0.0% |
| Arabic text with English total label | 2 / 6 | 48.4% | 52.6% |

Extracting all fields in the incorrect VAT example does not validate its
arithmetic; OCR transcription and financial verification are separate tasks.
`additional_samples.py` and `additional-samples-result.json` preserve the
experiment. It uses the separate Phase 13 synthetic PDFs and PyMuPDF. All
results require human review.

The script now accepts explicit `--pdf-dir`, `--tesseract`, `--tessdata`, and
`--output` paths, verifies the three PDF hashes and two pinned fast-model
hashes before running OCR, and refuses to overwrite a result.

New runs also record the executable and model hashes and a rendered-image
hash for each page. The PDF bytes hashed are the bytes rendered. The
executable and model files are checked again after the run; this is a
consistency check, not proof of executable authenticity or protection against
temporary replacement during execution. Older saved results lack these fields.

From a checkout containing the Phase 13 sample PDFs, with PyMuPDF and the
pinned language files installed separately, a Windows PowerShell example is:

```powershell
python experiments/phase15/additional_samples.py `
  --pdf-dir demo/samples/pdf `
  --tesseract 'C:\Program Files\Tesseract-OCR\tesseract.exe' `
  --tessdata '<local-pinned-tessdata-folder>' `
  --output '<new-result-file.json>'
```

Replace the two bracketed paths with local paths. The synthetic PDF result
was repeated locally with the same field counts and error rates. The original
Arabic-label image baseline still needs locally generated files and cannot be
reproduced from the checkout alone.

The two English PDF fixtures have different byte hashes in the canonical Git
blobs and in this Windows checkout with line-ending conversion. The script
accepts only these two explicitly recorded hashes per affected fixture and
records the actual hash used. Both local variants were tested. The Arabic
fixture has a single accepted hash. This does not make arbitrary modified PDFs
valid. The draft adds a Git attribute marking only `demo/samples/pdf/*.pdf`
as binary so future checkouts retain the committed bytes. A disposable Git
test checks the rule with Windows-style line-ending conversion. Existing local
files are not automatically replaced, and both recorded hashes remain
accepted for this experiment.

GitHub Actions also runs the three synthetic PDF cases on Ubuntu using the
official pinned fast models. It checks the PDF and model hashes, requires at
least five matched fields on each English page and nonempty Arabic OCR output,
and confirms the result requires human review. This is a smoke test, not an
Arabic accuracy threshold or evidence of production readiness. It uses the
runner's installed Tesseract version, which can differ from the local run.

## Reversed-label evaluation experiment

The Arabic PDF's OCR produced `AED :العملة`, while the original field
comparison recognized only a label before the colon. A separate experimental
comparison recognizes an exact known label on either side of one colon and
rejects duplicate recognized fields. On the existing OCR output for that
PDF, matching fields increased from 2 / 6 to 3 / 6 (supplier, currency,
and total). The earlier Arabic-label image remained at 2 / 6. The change
only handles one text-order issue; it does not improve OCR recognition or
recover the missing numeric fields.

`rtl_field_experiment.py` is an evaluation helper, not a production parser,
and has five local tests in `test_rtl_field_experiment.py`. It must not be
used to approve quotations or presented as a security-reviewed implementation.
This experiment is included in the draft PR but has not been integrated into the application. Further independent data and robust ambiguity handling are
needed before considering integration.

## Manually cropped number experiment

Four numeric regions in the first Arabic-label image were selected manually,
then run through the Arabic OCR model at two scales and two segmentation
modes. None of the 16 results exactly matched its expected Arabic-digit text.
This is a narrow exploration on one known image: the coordinates were chosen
by hand, so it is not an automatic field extraction method or an independent
test. It did not establish a usable improvement. No number was corrected or
approved based on these results.

The local `numeric_crop_experiment.py` and `numeric-crop-result.json` record
the coordinates, OCR output and exact text comparisons. The experiment
requires Pillow and the pinned local OCR models; it creates temporary crops
and refuses to overwrite its result file.

A later comparison used the same four manually selected number crops with both
the pinned fast and best Arabic models, three image scales and two page
segmentation modes: 48 runs in total. None matched the expected number after
strict Arabic-to-ASCII digit and decimal-point normalization. The comparison
does not guess letters, reorder digits, or interpret a comma as a decimal
point. These crops and settings were selected using the same known synthetic
image, so this result does not measure real-world accuracy. The observed
failure occurs even with the number region manually selected; text-order
handling alone does not fix this example. The local script and results are
`best_numeric_crop_experiment.py` and `best-numeric-crop-result.json`.

The official `tessdata_best` Arabic-script model (`script/Arabic`) was then
tested at the same pinned commit on that same image. Full-page OCR matched
2 / 6 fields, the same field count as the best Arabic language model. On the
24 manually selected number-crop runs, the script model correctly read the
VAT rate in 2 runs; none of the subtotal, VAT amount, or total crops matched.
This is an exploratory result on the same hand-selected example, not an
independent accuracy estimate or a basis for automatic decisions. Model bytes
were checked against the official Git blob and remain local; the experiment
and synthetic results are in `arabic_script_experiment.py` and
`arabic-script-result.json`.

An additional local experiment (`arabic_threshold_experiment.py`) applies
grayscale, contrast adjustment, 3x enlargement, a fixed threshold and a white
border to the same four hand-selected number regions. On this single
synthetic image, two best-model language choices and two segmentation modes
produced zero exact normalized numeric matches in 16 attempts. The recorded
`threshold-crop-result.json` is exploratory; it does not establish general
OCR accuracy or support using these values. Human review is still required.
CI checks the image preparation and refusal to overwrite a result, not this
local Tesseract run.

## Alternative local Arabic recognition experiment

An isolated Windows CPU test used PaddleOCR 3.3.2 and PaddlePaddle 3.2.0
with `arabic_PP-OCRv5_mobile_rec`. The [model documentation](https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html)
lists Arabic and English support; this does not establish accuracy on NAWA
documents. On the same four manually selected synthetic number crops, the
original and enlarged versions produced **0 / 8 strict numeric matches**.
The model transcribed some digits but emitted the Arabic comma `،` where the
reference has the decimal separator `٫`; the evaluator does not guess that
the two mean the same thing. Some outputs were incomplete or empty. Confidence
scores are model outputs, not calibrated correctness probabilities.

`paddle_arabic_crop_experiment.py` and `paddle-arabic-crop-result.json`
record the test, model file hashes, versions and outputs. The observed package
versions are in `paddle-qa-requirements-observed.txt`; this is not a locked or
audited dependency set. The model was downloaded into an isolated local
test directory and inference used local synthetic crops, not NAWA records.
Recorded hashes describe the files used; they are not independent vendor
authentication. The test does not cover automatic region detection, other
fonts, physical scans, independently reviewed ground truth, or deployment.
It provides no production accuracy claim and all results require human review.

A separate local full-page test (`paddle_arabic_page_experiment.py`) used the
PP-OCRv5 mobile detector with that Arabic recognizer, without manually chosen
crops. It detected eight lines on the same Arabic-label synthetic image. With
the same reference and normalization, its character error rate was 11.9%
and word error rate 42.3%; the earlier Tesseract run was 46.4% and 53.8%.
The experimental label-based field evaluators matched 0 / 6 fields for the
Paddle output versus 2 / 6 for the original Tesseract evaluation. Paddle
recognized words and some digits, but its output did not preserve the colons
required by these evaluators and contained numeric errors. The field score is
therefore a result of both recognition and the chosen parser, not a count of
all words recognized. One synthetic image, one run per engine, different
pipeline settings, and references authored with the fixture do not establish
general comparative accuracy. `paddle-arabic-page-result.json` records the
synthetic outputs and observed model hashes; no authenticity claim is made.
CI tests the evaluation helper, not the locally installed Paddle models.

An additional evaluation-only helper, `arabic_label_candidate_experiment.py`,
recognizes exact known Arabic labels at the beginning of a line even when the
colon is missing. It rejects duplicate labels, malformed numbers and
ambiguous numeric punctuation. Applied to the saved Paddle page output, it
matches the synthetic supplier name, or 1 / 6 fields; the five other fields
remain unmatched. This changes the parser evaluation, not the OCR output,
and the helper cannot promote or approve a quotation. The result and hash of
its saved input are in `arabic-label-candidate-result.json`. One hand-selected
sample cannot establish general accuracy or production safety.

The same local Paddle pipeline and candidate checker were also tried on page
1 of the repository's `arabic_text_supplier.pdf`, rendered with PyMuPDF
1.28.2 at 200 DPI. The PDF contains the same synthetic supplier and amounts
as the first example, so it is another layout, not independent test data.
The strict colon-based checker matched 1 / 6 fields (the English total), and
the exact Arabic-label candidate checker matched 2 / 6 (supplier and VAT
rate). The candidate checker handles Arabic labels only and its count is not
combined with the strict checker. The output still contained incomplete
currency and subtotal text and ambiguous punctuation in two amounts.
`paddle-arabic-pdf-result.json` records the synthetic outputs and observed
model hashes; `render_synthetic_arabic_pdf.py` can produce the pinned input
from the corresponding known-hash PDF. It refuses a different rendering or
an existing output file. Results remain human-review-only.

Two more synthetic pages with different supplier names and amounts were
generated locally using Windows GDI+ and Arial. They share one clean digital
layout, have fixture-authored references, and are not independently reviewed
or representative of scanned documents. On these exact pages, Tesseract
matched 2 / 6 fields on each using the strict label checker; Paddle matched
0 / 6 with that checker and 1 / 6 with the separate Arabic exact-label
candidate checker. These scores include parser behavior and are not a general
ranking of the engines. The source images, `manifest.json`, recorded local
outputs and hashes are in `arabic-new-synthetic-pages/` and
`synthetic-arabic-batch-result.json`; the observed batch used local CPU models.
`generate_synthetic_arabic_pages.ps1` documents generation using PowerShell 7;
fonts and rendering versions can change the output bytes, and the evaluator
accepts only the committed pinned images and manifest. CI verifies the saved
synthetic data and recalculates field matches, not a live Paddle inference.

`arabic_numeric_diagnostics.py` adds experimental review hints for exact
Arabic labels at the beginning of a line. It distinguishes a missing exact
label, duplicate label, missing value, Arabic comma ambiguity, malformed
numeric text, and a numeric-looking candidate. A candidate is **unverified**:
it can be incomplete or wrong even if its format is valid. The helper does
not correct punctuation, recognize misspelled or value-before-label text, or
approve a quotation. `arabic-numeric-diagnostics-result.json` shows its hints
for the saved two-page synthetic output; it is not connected to the portal.

`blind_synthetic_review.py` creates a new transcription packet containing
copies of the two pinned pages and a blank answer template. The packet does
not include expected values or OCR outputs. It checks image hashes and refuses
an existing destination. A reviewer can transcribe from the images or mark
values unclear, without guessing. The packet itself cannot authenticate a
reviewer, prove independence, establish accuracy, or approve a quotation.
Independent review and a representative evaluation set remain outstanding.

`compare_blind_transcriptions.py` compares a completed packet's supplied
transcriptions against the pinned synthetic fixture manifest. It separately
reports matching and differing values, blanks, reviewer-marked unclear values,
and numbers that cannot be compared safely. It verifies the manifest hash and
the page identities stated in the packet, but it does not authenticate the
reviewer, establish independence, verify that a reviewer actually viewed the
image, or approve a quotation. Matching uses the benchmark's normalization;
it is not a character-for-character transcription check. The untouched blank
packet reports every field as not transcribed, and no human review has yet
been claimed.

For human inspection, `synthetic_review_packet.py` can create a new local
packet for the same fixed synthetic image. It includes a copy of the original,
four manually selected number-region crops, source and crop SHA-256 hashes,
pixel coordinates, and an HTML review page. A reviewer can enter transcriptions
and download a JSON file in the browser; the file remains marked
`human_review_required` and does not record an approval. Entries are not saved
automatically. A Node-based test checks the download script using a simulated
DOM; a real-browser review has not been completed. It proposes no values or
approval. The regions are specific to this one fixture; this is not a general reviewer
interface, production evidence chain, or processor for real documents.

`validate_synthetic_review.py` checks a downloaded synthetic export against
the local packet: image and crop hashes, region metadata, and crop pixels
against the referenced coordinates. The command also checks the source image
hash and expected region labels and coordinates against constants for the
fixed synthetic fixture outside the packet. It rejects changed crops, inconsistent
metadata, unsafe crop paths and approval status. A successful result still
requires human review. This checks consistency only: the packet and export
are unsigned, and it cannot prove the reviewer's identity or the correctness
of their transcription. The anchor is only trustworthy if the code and its
fixture constants have been obtained and protected through trusted means.
The real-browser download test remains pending.

## Experimental intake handoff

The Phase 13 synthetic intake worker extracts selectable text and does not
invoke this OCR experiment. The Phase 15 draft adds a promotion guard to its
draft intake path: explicit OCR, unknown extraction types, review-state
markers, and OCR-marked evidence are rejected before promotion. Existing
synthetic text and text-layer PDF results remain eligible. This is not
deployed to the running portal.

`ocr_intake_handoff.py` defines a separate experimental handoff that produces
only `requires_human_review` and `promotable: false`, and records hashes without
creating a quotation or copying OCR text into the handoff. The caller supplies
the source PDF hash and page, which this function does not independently bind
to the image. The contract is not connected to intake. The new marker guard
rejects its explicit review state, but cannot prove provenance: legacy text
results without an input-type marker are still accepted, and a mislabeled
result could bypass marker checks. Actual rendering provenance, authenticated
producer identity, authorization, review persistence, and an independently
reviewed promotion policy remain open.

New results from the synthetic text worker now receive the server-assigned
`synthetic_text_worker_v1` origin after the worker checks that the parser output
has no OCR or review markers. OCR-marked parser output fails rather than being
relabelled. The promotion guard rejects any other explicit origin but still
accepts legacy unmarked text records for compatibility. The marker is not
cryptographic proof or authenticated worker identity, and a compromised or
incorrect producer could mislabel content. No OCR worker is integrated.

An additive synthetic PostgreSQL migration adds a nullable `result_origin`
column separate from result JSON. New completed text-worker jobs copy the
origin into the column in the same completion transaction; promotion rejects
an inconsistency between the column and JSON. Existing rows remain unchanged
and unmarked (`NULL`), and unmarked legacy results remain eligible for the
existing text-only policy. Requeue clears the column with the result.
The column is populated from the worker result, so this detects later
JSON-only changes; it is not independent worker attestation, and a database
writer able to change both values can still mislabel a result. The migration is
explicit and only for the disposable synthetic environment; it has not been
applied to the user's databases. Upgrade and rollback planning, authenticated
worker identity and deployment policy for legacy records remain open.

The synthetic intake draft offers an explicit server-side `require_recorded`
origin policy. Under it, legacy unmarked records remain readable but cannot be
promoted; matching recorded text-worker results remain eligible. The default
`legacy_compatible` policy preserves existing behavior. The synthetic
container reads `NAWA_SYNTHETIC_ORIGIN_POLICY` at startup, rejects unknown
values before connecting to the database, and does not accept the policy from
an HTTP request. The isolated Phase 13 QA Compose configuration selects
`require_recorded` for both synthetic tenants; the live portal is unchanged.
This checks recorded markers, not authenticated worker identity, and cannot
protect against a database writer changing both stored values.

`synthetic_worker_receipt.py` explores an HMAC receipt bound to a synthetic
tenant, document ID, job ID, source hash, result hash, origin and key ID. Tests
reject changes to those values, a wrong key and cross-job or cross-tenant
substitution. It is a standalone Python-only experiment: it is not wired to
intake or promotion and does not authenticate a real worker. The receipt
verifier alone does not prevent replay within the same job. HMAC verifiers with the shared key can also create
receipts. Trusted key provisioning, rotation, compromise recovery, atomic
recording, replay protection, interoperable serialization and security review
must be designed before any production claim.

`synthetic_receipt_ledger.py` separately demonstrates one-time receipt
consumption in a disposable SQLite database. It verifies a receipt, marks the
synthetic job consumed, and records a result hash and test audit event in one
transaction; tests cover replay, concurrent attempts, wrong keys, altered
results, restart, and rollback when event insertion fails. The event is not
tamper-proof or append-only. The test database stores neither the
synthetic key nor raw result. This ledger is not wired to PostgreSQL, intake,
or promotion; it does not address key provisioning, database tampering,
worker authentication, backup rollback, distributed operation, or production
replay protection.

`synthetic_pg_receipt_ledger.py` is a separate disposable PostgreSQL
experiment of the same one-time receipt and event transaction. It checks for
a QA database-name prefix and uses a newly generated synthetic schema. That
name check alone does not prove a database is disposable and is not an access
control. GitHub CI provisions a dedicated disposable database for these
tests; do not point the experiment at saved NAWA data. It is not wired into
the intake worker or promotion. A synthetic test backs up a separate
application database before receipt consumption, restores that stale backup,
and checks that a preserved receipt ledger rejects the duplicate. A second
test shows the trade-off: if ledger consumption commits but application work
does not, retries are blocked and reconciliation is required. These tests rely
on preserving the ledger separately; restoring or tampering with the ledger
can defeat the demonstration. Key management, authenticated producers,
cross-database failure handling and protection from database writers remain
unresolved.

`synthetic_reconciliation.py` classifies supplied synthetic ledger and
application snapshots without taking any action. A consumed receipt with a
pending application job is marked for manual reconciliation; matching completed
hashes are reported only as matching observations. Missing, malformed, or
conflicting observations do not trigger a retry. Tests exercise the stale
restore and stranded-job examples. The observations may be read at different
times, so this is not a consistent cross-database snapshot, an operator
workflow, or an authorization to repair records.

`synthetic_reconciliation_inspector.py` reads the experimental ledger and
synthetic application job in separate PostgreSQL read-only transactions and
passes the observations to that classifier. A missing record or unavailable
database never triggers a retry; error details are not returned. The CI test
uses disposable databases on the same server, checks tenant scoping, and
confirms the observed states are not modified. It also creates a synthetic
PostgreSQL login with a generated test-only password, grants SELECT on the two
test tables, checks that a wrong password fails, and checks that UPDATE and
ungranted event-table reads are denied. This exercises authentication and
database privileges in the disposable test cluster; it does not establish
real deployment permissions or credential management. The test also enables
row-level security on both synthetic tables, binds each of two test tenants to
its database login name, and checks that both tenants' rows are hidden from
one another even when directly queried. It also checks that neither login can
switch into the other's role, that a client-supplied tenant setting does not
change the login identity, and that requesting `row_security=off` results in
an error rather than disclosure. This one-login-per-test-tenant model is an experiment,
not the NAWA application's tenant authorization design; administrators and
roles with RLS bypass privileges require separate controls. A database-name prefix is not
a security boundary. This code is not connected to NAWA, and it does not
provide an atomic cross-database snapshot or a production reconciliation
process.

An experimental session broker selects the database connection from a
server-owned tenant mapping after checking a synthetic in-memory session and
its current membership. It accepts no client-selected tenant and has no HTTP
endpoint. The disposable PostgreSQL test uses manually issued test sessions
and two test database roles. This does not establish integration with a real
identity provider. Membership can be revoked after the check while a request
is in flight, so the broker checks the session and membership again after
inspection and discards the result if they changed. This still cannot make
revocation atomic with response delivery. Production credential management
remains open.

The disposable PostgreSQL backup/restore test also checks that the separate
origin survives restore, and that a JSON-only origin change in the restored
test copy is rejected without changing its existing human review. This does
not verify a production backup, recovery time objective or external storage.

The synthetic PostgreSQL integration suite includes a case that inserts an
explicit OCR marker into a disposable test record, checks that promotion
creates no quotation or promotion row, then restores the original synthetic
text result and confirms it can be promoted. This tests marker enforcement,
not the ability to detect an OCR result that has been mislabeled as text.

## Official fast versus best language models

The official `tessdata_best` Arabic and English models at commit
`e12c65a915945e4c28e237a9b52bc4a8f39a0cec` were downloaded into a separate
local folder, checked against upstream Git blob IDs, and compared with the
pinned `tessdata_fast` models. The same existing synthetic images, reference
transcriptions, page segmentation mode 6, and original label-first field
comparison were used. The results are single local runs:

| Case | Fast fields / CER | Best fields / CER |
| --- | --- | --- |
| English scan | 6 / 6; 0.0% | 6 / 6; 0.0% |
| Arabic-label image | 2 / 6; 46.4% | 2 / 6; 33.9% |
| Arabic text PDF page | 2 / 6; 48.4% | 2 / 6; 40.3% |

The best model reduced character error on these Arabic examples, but did not
increase the exact field count under this comparison. The earlier experimental
reversed-label comparison was not applied here. This is not an independent
accuracy study, and the numbers remain unsuitable for automatic approval.
`compare_best_model.py` and `best-model-comparison.json` contain the local
experiment, timing and model provenance. Models and synthetic images are not
in the PR. Source: https://github.com/tesseract-ocr/tessdata_best/tree/e12c65a915945e4c28e237a9b52bc4a8f39a0cec

## Provenance and reproduction limits

- Tesseract executable: local Windows Tesseract 5.4.0.
- Language model source: [official tessdata_fast repository](https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd),
  pinned to commit `87416418657359cb625c412a48b6e1d6d41c29bd`.
- Language-model license: [Apache 2.0](https://github.com/tesseract-ocr/tessdata_fast/blob/87416418657359cb625c412a48b6e1d6d41c29bd/LICENSE);
  a copy was downloaded beside the local test models.
- The model files were verified against their upstream Git object IDs and
  their SHA-256 hashes are recorded in the result and script.
- The local Arabic PDF uses a Windows system font. The PDF, raster images,
  downloaded language models and system font are **not** in this repository.
  The script pins the local image hashes and fails if they change.
- `ocr_benchmark.py` is an offline, fixed-fixture measurement script, not
  an OCR service or secure document processor. It requires the specified
  local Tesseract executable, model files and synthetic images. It refuses to
  overwrite an existing result. The original two-image benchmark is local;
  CI runs the separate three-PDF synthetic engine smoke test described above.

## Remaining Phase 15 work

`synthetic_dataset_manifest.py` is an experimental, synthetic-only metadata
validator. It checks declared creator and reviewer identifiers, license
reference, language, content hash and split, and rejects source IDs or hashes
shared between development and evaluation splits. An optional function checks
caller-supplied sample bytes against the declared hashes and requires the exact
sample set. It does not read files, establish the origin of bytes or hashes,
authenticate reviewers, establish license rights,
or verify ground truth. Metadata passing the check is not evidence that a
dataset is representative, independently reviewed, accurate, or suitable
for production. A curated bilingual dataset and independent review remain
necessary.

An isolated local single-image OCR prototype now exists in
`bounded_ocr_prototype.py`. It requires an explicit call and configured
executable/models, checks PNG size and dimensions, limits elapsed process time
and captured output, restricts language choices, and marks its output for
human review. It passes a temporary copy of the validated bytes to OCR so a
later change to the original file does not change the content being read.
Eight local checks cover this behavior, timeouts, excess output, failure,
invalid images, dimensions and language selection. Local Tesseract smoke tests
matched 6 / 6 fields on the existing synthetic English image and 2 / 6 on the
existing Arabic-label image. This prototype is included in the draft PR but is not integrated with NAWA.

A separate opt-in wrapper checks caller-supplied model SHA-256 hashes before
and after OCR and records those hashes and the engine's self-reported version.
Fifteen local tests now pass, including changed and incorrect model files; an
English synthetic Tesseract smoke test passed using the pinned fast model.
These checks do not prove the engine binary's identity or prevent a model from
being swapped and restored between checks. Docker access was unavailable in
the current session, so container isolation has not been tested here.

An additional opt-in wrapper compares the executable's SHA-256 with a
caller-provided value before and after OCR and records the hash. Tests reject
an incorrect hash and a changed executable. This is not signature
verification, does not prevent swapping and restoring during execution, and
depends on obtaining the expected digest from a trustworthy source. The local
smoke test derives its comparison hash from the same local file, so it checks
consistency during that test, not the executable's authenticity.

The output reader also has a deadline if a descendant retains its pipe after
the parent exits. A synthetic subprocess test confirms the caller returns an
error rather than waiting indefinitely. This does not terminate descendants;
they may outlive the call, so process-tree isolation and cleanup remain open.

An additional local Windows-only experiment reused the original NAWA
launcher's `WindowsJob` class without modifying that workspace. A disposable
synthetic parent was held at a gate until it was attached to a job, then
spawned a child; closing the job ended the parent and closed the child's
inherited output pipe. The test passed in this Windows environment. This is
not integrated into the OCR prototype: attaching an already running OCR
process has a race before assignment, and sandboxing, failure handling,
nested-job compatibility and independent review are still needed.

A follow-up local Windows experiment (`windows_gated_launcher_experiment.py`)
starts an isolated Python starter that waits for a signal, attaches that
starter to a Windows cleanup job, then allows it to launch a synthetic
child. Three local tests passed: the child is not started before assignment,
an assignment failure prevents launch, and closing the job stops a started
child. The gated starter addresses the tested child-before-assignment race,
but it is a prototype: it relies on a trusted Python runtime, is not connected
to the NAWA OCR workflow, and is not a sandbox. Breakaway
processes, CPU/memory limits, nested-job environments, output handling and
other failure paths need independent security and platform review.

The gated-launch experiment now includes a minimal Windows job implementation
in `windows_cleanup_job.py`. Its real cleanup test no longer needs the original
NAWA launcher file and is configured to run on Windows CI. The two assignment
tests use a test double. Linux skips the three Windows-only tests, and CI does
not run the local Tesseract smoke test.

The gated starter has also been used in `gated_ocr_smoke.py` to run the local
Tesseract executable on the two existing hash-pinned synthetic images. The
English result matched 6 / 6 fields and the Arabic-label result 2 / 6, the
same counts as the baseline. The smoke test closes the job after the gated
process exits and before reading its output. This is a fixed local test, not
an OCR service, an integration with NAWA, or evidence of process sandboxing.

`windows_gated_bounded.py` combines the gated starter, job cleanup, elapsed
time limit, and captured-output limit for explicitly supplied trusted test
commands. The Windows job now also limits active processes and total committed
job memory, with defaults of four processes and 512 MiB. It now also requests
a Windows CPU hard cap of 50%; CPU limits in nested jobs are relative to the
parent job. Nine local Windows checks passed, covering output, timeouts, process
and memory limits, CPU configuration, errors,
and termination of a synthetic descendant after its parent exits. A local
synthetic English Tesseract smoke test matched 6 / 6 fields. It remains an
experiment: the CPU setting has been queried but its effective performance
has not been benchmarked. It does not protect against job breakaway,
establish executable authenticity or handle
untrusted documents. The local OCR prototype can now explicitly receive this
runner; the default remains the original local subprocess runner, and neither
path is wired to NAWA. `windows_synthetic_ocr_smoke.py` tested the combined
prototype locally on both pinned fixtures: English 6 / 6 and Arabic 2 / 6,
with human review required. The combined Tesseract path is not tested in CI.
An explicitly selected `windows_image_validation.py` validator now runs PNG
decoding in a separate job-limited process. It checks PNG structure and then
loads image pixels; structural verification alone does not detect every
corrupt compressed image. Four tests cover valid, corrupt, damaged pixel data,
and oversized synthetic images. The original default validator still decodes
in the calling process. The new validator relies on the local Python and
Pillow installation, uses temporary files, and provides resource cleanup, not
a security sandbox or a guarantee against malicious images. It is not
connected to the NAWA application.

Three Windows end-to-end tests use a controlled synthetic engine to exercise
the validated image copy, executable and model-hash checks, gated Windows runner,
job cleanup, review-required status, and engine failure behavior. They test process
plumbing, not OCR accuracy or the real Tesseract executable.

This prototype is **not a security boundary**: it has not been independently
reviewed and does not sandbox image decoding or Tesseract or defend its
temporary copy from a hostile local process. The original default
runner does not provide Windows job memory or process-tree controls; the gated
runner's controls require further security review. It lacks verified engine
identity, full page-level provenance and a production
worker interface. It must not be used for untrusted or real documents.

Complete a properly isolated, opt-in bounded OCR worker; curate a licensed, representative
Arabic and English dataset with independently reviewed ground truth;
evaluate character, word and field accuracy by script and scan quality;
record page-level provenance, engine/model versions and review-needed states;
and evaluate runtime and failure handling. Do not claim the Phase 15 gate
has passed from these two samples.
