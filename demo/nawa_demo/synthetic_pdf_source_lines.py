"""Extract raw lines from two pinned synthetic PDFs; never run OCR."""
import hashlib
import json
import sys

from .intake_limits import apply_parser_limits

ARABIC_SHA256 = 'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68'
MULTIPAGE_SHA256 = '3bbebac92722b82770c31725806efb6148f2b317b0a3af7348145a2f336d95d6'
MAX_PDF = 4 * 1024 * 1024
MAX_TEXT = 1024 * 1024


def main():
    apply_parser_limits()
    content = sys.stdin.buffer.read(MAX_PDF + 1)
    digest = hashlib.sha256(content).hexdigest()
    if len(content) > MAX_PDF or digest not in (ARABIC_SHA256, MULTIPAGE_SHA256):
        raise ValueError('Unsupported synthetic PDF fixture')
    if digest == ARABIC_SHA256:
        import pymupdf
        with pymupdf.open(stream=content, filetype='pdf') as document:
            if document.needs_pass or document.page_count != 1:
                raise ValueError('Unsupported synthetic PDF structure')
            pages = [document[0].get_text('text', sort=True)]
    else:
        from .intake_pdf import open_pdf
        document = open_pdf(content)
        if document.is_encrypted or len(document.pages) != 2:
            raise ValueError('Unsupported synthetic PDF structure')
        pages = [page.extract_text() or '' for page in document.pages]
    if not any(page.strip() for page in pages) or sum(len(page.encode('utf-8')) for page in pages) > MAX_TEXT:
        raise ValueError('Synthetic PDF text unavailable')
    lines = [{'text':line, 'page':page_number, 'page_line':line_number}
             for page_number, text in enumerate(pages, 1)
             for line_number, line in enumerate(text.splitlines(), 1)]
    sys.stdout.buffer.write(json.dumps(lines, ensure_ascii=False).encode('utf-8'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # No document or parser details are written to stderr.
        raise SystemExit(1) from None
