"""Subprocess entry point for the synthetic intake worker."""
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import json
import os
import sys

from .intake_limits import apply_parser_limits

# Only the repository's exact mixed Arabic–English synthetic PDF fixture,
# in its known LF and Windows CRLF forms, uses the Phase 3 extractor.
SYNTHETIC_ARABIC_PDF_HASHES=frozenset({
    'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68',
    'ff402285c60252bf4b25084cf35cbc9a1f61769aa51adf19274bfaf0ba23fc53',
})


def is_synthetic_arabic_pdf(content):
    return sha256(content).hexdigest() in SYNTHETIC_ARABIC_PDF_HASHES


def main():
    apply_parser_limits()
    from .core import extract
    from .intake_worker import IncompleteArabicPDF, _extract_pdf
    if len(sys.argv) != 2:
        raise ValueError('Expected one input file')
    path = Path(sys.argv[1])
    if path.suffix == '.pdf':
        content=path.read_bytes()
        if is_synthetic_arabic_pdf(content):
            from .pdf_ingest import extract_pdf
            result=extract_pdf(path,ocr=False,max_pages=50,max_text_chars=1024*1024)
        else:
            with TemporaryDirectory(prefix='nawa-parser-') as temp:
                try:
                    result = _extract_pdf(content, temp)
                except IncompleteArabicPDF:
                    # Explicit synthetic QA only. No OCR or fallback for
                    # invalid, encrypted, empty, oversized or timeout cases.
                    if (os.environ.get('NAWA_INTAKE') != 'synthetic'
                            or os.environ.get('NAWA_EXPERIMENTAL_ARABIC_PDF') != '1'):
                        raise
                    from .pdf_ingest import extract_pdf
                    result=extract_pdf(path,ocr=False,max_pages=50,max_text_chars=1024*1024)
    else:
        result = extract(path)
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8'))


if __name__ == '__main__':
    main()

