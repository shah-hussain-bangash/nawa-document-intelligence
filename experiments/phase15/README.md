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
  overwrite an existing result. The repository CI runs metric unit tests,
  not this model-dependent measurement.

## Remaining Phase 15 work

Build an opt-in bounded OCR worker; curate a licensed, representative
Arabic and English dataset with independently reviewed ground truth;
evaluate character, word and field accuracy by script and scan quality;
record page-level provenance, engine/model versions and review-needed states;
and evaluate runtime and failure handling. Do not claim the Phase 15 gate
has passed from these two samples.

