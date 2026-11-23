# Draft review set: three synthetic quotations

This is a small **development** set, not the proposed bilingual holdout or an independently reviewed benchmark. Labels are draft transcriptions from three fixed repository TXT files. There are two English examples, one Arabic example, no scanned PDFs, no mixed-language documents and no holdout split.

| Synthetic source | What to check | Draft expected result |
| --- | --- | --- |
| `english_quote.txt` | Supplier, currency and lines 3–6 | Subtotal AED 1000.00; VAT 50.00 at 5%; total 1050.00. Both arithmetic checks pass. |
| `arabic_quote.txt` | Arabic labels and Arabic-Indic digits on lines 1–6 | Subtotal AED 900.00; VAT 45.00 at 5%; total 945.00. Both arithmetic checks pass. |
| `incorrect_vat_quote.txt` | Values as printed, including the discrepancy | Subtotal AED 800.00; stated VAT 30.00 at 5%; total 830.00. VAT-rate check fails; addition check passes. |

The draft expected values are in `demo/samples/evaluation/draft_field_review.json`. A separate fluent reviewer should compare each label and line to the original, record disagreements and adjudication outside this fixture, and never mark this set independently reviewed based solely on the code output. The fixed text examples do not establish real-world accuracy or OCR performance.

From `demo`, run the local development replay:

```powershell
python -m nawa_demo.synthetic_field_baseline
```

The replay accepts only the three pinned synthetic source files, checks their LF-normalized hashes, parses verified copies and reports field accounting and arithmetic outcomes. It does not modify the sources. A matching draft label does not prove source meaning, applicable tax treatment or benchmark quality. The broader evaluation still needs a representative, separately reviewed holdout and documented access/lifecycle tests.
