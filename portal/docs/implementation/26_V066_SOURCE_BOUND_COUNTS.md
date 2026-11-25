# v0.6.6 — Source-bound quotation counts

## Reported failure and correction

Real Qwen3:8b trials returned cited Arabic answers that confused quotation counts
with prices, omitted the count after source reordering, or called an English
procurement policy an HR policy. A valid citation number did not establish factual
support. Neither experimental prompt was accepted as the application prompt.

Quotation-count questions now use a bounded extraction path after the existing
permission/domain/language-scoped retrieval. Recognised English and Arabic minimum
statements are read directly from Procurement/Policy passages. The result explicitly
states the count and cites the relevant original passages. It makes no generation
request, so this path works with MODEL_MODE=ollama, hosted or extractive without
sending those passages to a generation provider. Hybrid retrieval, when enabled,
still calls its configured embedding service under its existing class restrictions.

Every supporting passage must match the current document ID, version, page and
literal source text. For conflicting minima, the answer lists both values and
source names read from stored document metadata, reports conflicting evidence and
asks the reader to establish the applicable policy. It never chooses one count
based on language or source order. Missing or unrecognised minimum wording returns
the passages with an unverified-requirement message, rather than inventing a value.
The UI labels a verified result "Verified source count" and shows policy-specific
guidance for missing or conflicting counts. Original citation text is preserved.

This is an alternative source-extraction path for a narrow question type, not
general verification of arbitrary generated prose. General model questions retain
the existing adapter and its limitations; the experimental prompts are not installed.
Supplier bank/contact field checks still run first. The new output reason/count
facts do not add raw policy content to audit events.

## Apply to the existing v0.6.5 workspace

Stop the Nawa READY terminal with Ctrl+C; keep Ollama running. Extract the patch
and place both items beside nawa.py:

* apply_count_fix_v066.py
* count_fix_v066/

The source updater verifies every target's base/payload hashes before writing,
backs up previous source under .data/update-backups, and refuses custom targets
or an active launcher. Config, database, uploads and models are not payload files.
The patch targets v0.6.5. Do not force an update if a base-source check fails.

```powershell
py -3.12 apply_count_fix_v066.py
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py setup --stop-running
    if ($LASTEXITCODE -eq 0) {
        py -3.12 nawa.py run --auto-ports
    }
}
```

Use the existing .env, including the already configured Ollama and hybrid settings.
There is no dependency or schema change. Setup rebuilds the frontend metadata and
UI; it does not reset saved data. Launch from a terminal whose PATH can find the
installed OCR tools, using the existing refresh command if needed.

In Knowledge assistant ask the original Arabic question:

```text
كم عرض سعر صالح يلزم قبل الموافقة التجريبية؟
```

With the seeded policy, the answer should explicitly give **2**, display "Verified
source count", and cite the policy. Reordering source passages must not omit it.
Conflict and unsupported-format coverage is exercised by the shipped regressions;
do not edit active policies or saved cases just to manufacture a test conflict.
General generation can still produce incorrect answers and needs source review.

## Bounds and acceptance

The recogniser handles a bounded set of English/Arabic quotation-count question
phrases and explicit "at least"/"على الأقل" statements. English integer words one
through twenty, Arabic one through ten and explicit dual forms, and integer digits
1–1000 are recognised. Arabic digit/diacritic normalisation is used for matching;
the original evidence is never rewritten. Unsupported forms, exact/maximum counts,
negation, conditional/per-supplier requirements and relevant unparsed clauses are
withheld for review. It does not determine policy authority, effective dates,
jurisdiction, budget thresholds, tables or general semantic entailment. Readable
source content can still be wrong; human review remains necessary.

Minimum-price/value questions and compound count/value questions do not use this
count recogniser. They retain the existing route; a minimum price is never
presented as a verified quotation count.

Regression fixtures are reconstructed from the user's synthetic capture, with
recorded JSON provenance. They include two/three/four, English/Arabic, shuffled
citations, absent/conflicting counts, literal page/version checks and real API
tenant/role exclusion. Passing these selected developer cases is not a held-out
bilingual generation benchmark or production acceptance. The existing captured-score
retrieval replay remains separate from answer correctness.
