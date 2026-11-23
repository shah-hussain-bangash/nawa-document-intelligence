# Synthetic quotation field metrics

This offline accounting experiment reports exact canonical-value matches for supplier, reference, currency, subtotal, VAT rate, VAT amount and total, separately for Arabic, English and mixed-language cases. It counts expected present fields, correct values, missing predictions and incorrect predictions. For fields labeled absent, it separately counts unexpected predictions. A field with no expected present values has a `null` exact-match rate instead of an invented percentage.

The caller supplies already normalized string values and names the normalization policy. The scorer does not infer whether Arabic and English numeric forms are equivalent, check source documents or determine which labels are correct. Every label is self-declared, including those marked `reviewed`. Only synthetic cases are accepted, and the output contains aggregate counts rather than source text.

The tests exercise accounting on hand-authored examples. No independent holdout, real model run, OCR score, release threshold or measured supplier-document accuracy is established by this module. Before reporting quality, freeze a lawful dataset, document normalization and missing-field conventions, obtain independent bilingual review, record source provenance and evaluate the actual pipeline.
