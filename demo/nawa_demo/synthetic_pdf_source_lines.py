"""Extract raw lines only from one pinned synthetic PDF; never run OCR."""
import hashlib
import json
import sys

from .intake_limits import apply_parser_limits

PDF_SHA256 = 'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68'
MAX_PDF = 4 * 1024 * 1024
MAX_TEXT = 1024 * 1024


def main():
    apply_parser_limits()
    content = sys.stdin.buffer.read(MAX_PDF + 1)
    if len(content) > MAX_PDF or hashlib.sha256(content).hexdigest() != PDF_SHA256:
        raise ValueError('Unsupported synthetic PDF fixture')
    import pymupdf
    with pymupdf.open(stream=content, filetype='pdf') as document:
        if document.needs_pass or document.page_count != 1:
            raise ValueError('Unsupported synthetic PDF structure')
        text = document[0].get_text('text', sort=True)
    if not text.strip() or len(text.encode('utf-8')) > MAX_TEXT:
        raise ValueError('Synthetic PDF text unavailable')
    sys.stdout.buffer.write(json.dumps(text.splitlines(), ensure_ascii=False).encode('utf-8'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # No document or parser details are written to stderr.
        raise SystemExit(1) from None
