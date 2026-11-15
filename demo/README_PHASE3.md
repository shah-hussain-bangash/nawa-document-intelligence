# Phase 3: Arabic PDF text and opt-in OCR fallback

This incremental, synthetic-data demonstration builds on Phase 2. The same strict `label: value` quotation parser and financial validation are reused. PyMuPDF reads selectable text; when `--ocr` is explicitly provided, Tesseract processes pages with no selectable text. Each field retains page and extracted-line evidence and now includes a `method` (`text_layer` or `ocr`).

## Install

From the repository root:

```bash
python3 -m pip install -r demo/requirements-pdf.txt
```

For optional OCR, install **Tesseract** and language data on macOS (Homebrew):

```bash
brew install tesseract tesseract-lang
# Confirm installed languages:
tesseract --list-langs
```

Confirm `eng` and `ara` appear before using `--langs eng+ara`. Python packages alone cannot provide the Tesseract binary or languages.

## Run

```bash
cd demo
python3 -m nawa_demo.pdf_cli samples/pdf/english_supplier.pdf samples/pdf/arabic_text_supplier.pdf
python3 -m nawa_demo.pdf_cli samples/pdf/scanned_english_supplier.pdf samples/pdf/arabic_text_supplier.pdf --ocr --langs eng+ara
python3 -m unittest discover -s tests -v
```

## Supported scope and limitations

- Arabic **selectable-text** extraction is demonstrated with a synthetic mixed-language PDF (five Arabic fields and an English grand-total label), using Arabic-Indic numbers. This does not demonstrate an Arabic-only quotation.
- The OCR sample demonstrates **English scanned** text only; Arabic scanned accuracy is not benchmarked.
- OCR is opt-in: without `--ocr`, image-only documents raise `PDFTextUnavailable`.
- OCR errors are possible; human verification is required for extracted values. No OCR confidence or accuracy benchmark is claimed.
- Text line/page evidence does **not** locate a precise bounding box or prove semantic accuracy.
- Complex tables, mixed layouts, PDF protection, tenant permissions, LLMs and RAG remain outside this starter.
- The parser still requires fixed, recognizable labels and AED currency.
- The test suite may skip OCR integration if Tesseract is absent. A skip is **not** a pass.
- Use synthetic data only; never upload private supplier quotations.
