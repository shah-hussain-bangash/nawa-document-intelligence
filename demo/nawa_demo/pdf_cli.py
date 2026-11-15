"""Run with: python -m nawa_demo.pdf_cli PDF1 PDF2 [--ocr] [--langs eng+ara]."""
import argparse
from pathlib import Path
from .core import write_json
from .pdf_ingest import OCRUnavailable, compare_pdfs


def main():
    parser = argparse.ArgumentParser(description="NAWA synthetic PDF quotation demo")
    parser.add_argument("quotations", nargs="+", type=Path, help="Quotation PDFs")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    parser.add_argument("--ocr", action="store_true", help="Run Tesseract on pages without a text layer")
    parser.add_argument("--langs", default="eng+ara", help="Tesseract language codes, e.g. eng+ara")
    args = parser.parse_args()
    try:
        print(write_json(compare_pdfs(args.quotations, ocr=args.ocr, languages=args.langs), args.output))
    except (OSError, ValueError, OCRUnavailable) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
