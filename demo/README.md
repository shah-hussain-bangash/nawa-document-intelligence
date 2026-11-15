# NAWA synthetic quotation comparison demo

This **runnable, standard-library-only Python demonstration** extracts a small fixed set of fields from explicitly formatted Arabic/English **UTF-8 text** quotations, checks VAT/total arithmetic with `decimal.Decimal`, records source-line evidence, and compares valid totals.

**Not implemented here:** PDF ingestion, OCR, page/bounding-box citations, LLM extraction, RAG, identity/tenant authorization, cloud deployment or production validation. The sample files are synthetic. This is not the full NAWA platform.

## Requirements

- Python 3.10 or newer
- No third-party packages or external services

## Run

From the repository root:

```bash
python3 -m demo.nawa_demo demo/samples/english_quote.txt demo/samples/arabic_quote.txt
```

Or run from inside `demo`:

```bash
cd demo
python3 -m nawa_demo samples/english_quote.txt samples/arabic_quote.txt --output result.json
```

> Note: The first command uses `demo` as a namespace package. You can also simply run `cd demo` and use the second command.

The JSON output includes the original supplier name, numeric fields, validation flags, and evidence as the line number and text from each synthetic source. The `lowest_valid_total` field is **a price-only comparison**, not an award recommendation.

To demonstrate a caught discrepancy:

```bash
cd demo
python3 -m nawa_demo samples/english_quote.txt samples/incorrect_vat_quote.txt
```

## Tests

From inside the `demo` directory:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover Arabic-Indic numeric digits, English extraction, VAT mismatch, missing and repeated fields, unsupported currency, ranking, and input count. The CI workflow executes these same tests.

## Important limitations

- This rules-based parser requires fixed `label: value` input lines and recognizes only selected Arabic/English labels.
- It only accepts AED quotations and does not handle real-life quotation layouts, rounding conventions, credit notes, invoices, pricing units or tax exemptions.
- Evidence is **line-level**, not page- or bounding-box-level.
- Neither OCR/extraction accuracy nor RAG retrieval performance can be inferred from these samples or tests.
- No confidential or real supplier documents should be added to the repository.
