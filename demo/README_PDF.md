# NAWA - page-aware text PDF extraction (phase 2)

This optional upgrade adds support for **text-layer** PDFs. It extracts PDF text with PyMuPDF, feeds it to the existing `nawa_demo.core.extract` parser and records page plus page-line evidence. It does not add OCR, and it does not change the original text demo.

## Install and run

From the repository root on macOS:

```bash
cd ~/nawa-document-intelligence
python3 -m pip install -r demo/requirements-pdf.txt
cd demo
python3 -m nawa_demo.pdf_cli samples/pdf/english_supplier.pdf samples/pdf/second_page_supplier.pdf --output pdf_result.json
python3 -m unittest discover -s tests -v
```

Synthetic PDF samples are in `samples/pdf/`. They contain selectable **English** text; one spans two pages, and one image-only PDF demonstrates an explicit OCR-needed failure. The original `samples/arabic_quote.txt` continues to test Arabic-Indic digits and fields in text input.

Expected lowest valid total: `Example Page Two Supplies` (AED 945.00). Existing English example total: AED 1,050.00.

## Scope and evidence

- Page references are **1-based**; `page_line` denotes line number in extractor output, not visual coordinates.
- The `line` field remains flattened extracted-text line number for compatibility with the original parser.
- Fixed `label: value` layout is mandatory; real supplier quotations often have tables, multiple columns, annotations, and OCR noise.
- Arabic **PDF** extraction is not validated by the included fixtures; Arabic text input is supported by the original stage only.
- No OCR, bounding-box coordinates, retrieval, citations from RAG, authentication, or production validation.
- Test fixtures are intentionally synthetic. Never upload confidential supplier documents.

## Error handling

Image-only PDFs produce `No extractable text... need OCR`, instead of pretending to parse values. Malformed PDFs and missing financial fields are rejected with clear errors.
