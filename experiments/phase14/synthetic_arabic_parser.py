"""Bounded, synthetic-only entry point for the existing bilingual PDF parser."""
import json
from pathlib import Path
import sys

from nawa_demo.intake_limits import apply_parser_limits


def main():
    apply_parser_limits()
    from nawa_demo.pdf_ingest import extract_pdf
    if len(sys.argv) != 2:
        raise ValueError('Synthetic PDF required')
    result=extract_pdf(Path(sys.argv[1]),ocr=False)
    sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8'))


if __name__=='__main__':
    main()

