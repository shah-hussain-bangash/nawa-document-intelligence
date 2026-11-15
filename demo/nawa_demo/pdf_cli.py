"""Run with: python -m nawa_demo.pdf_cli PDF1 PDF2 [--output result.json]."""
import argparse
from pathlib import Path
from .core import write_json
from .pdf_ingest import compare_pdfs


def main():
    parser = argparse.ArgumentParser(description="NAWA text-layer PDF quotation demo (no OCR)")
    parser.add_argument("quotations", nargs="+", type=Path, help="Text-based quotation PDFs")
    parser.add_argument("--output", type=Path, help="Optional JSON result path")
    args = parser.parse_args()
    try:
        print(write_json(compare_pdfs(args.quotations), args.output))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
