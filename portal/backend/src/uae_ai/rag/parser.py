"""Isolated bounded extraction with optional local English/Arabic OCR."""
import json
import os
import sys
from pathlib import Path
import subprocess
try:
    import resource
except ImportError:  # Native Windows: use Docker for OS-enforced parser limits.
    resource = None


def parse(path, *, ocr_mode="auto", languages="eng+ara", max_ocr_pages=6):
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8")
        pages = [{"page": 1, "text": text[:200000], "method": "text", "warnings": []}]
    else:
        from pypdf import PdfReader
        from uae_ai.rag.ocr import capabilities, recognise_page
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted or len(reader.pages) > 60:
            raise ValueError("Encrypted documents and PDFs over 60 pages are unsupported")
        pages, attempted = [], 0
        tools = capabilities(languages) if ocr_mode == "auto" else {"ready": False}
        for number, source in enumerate(reader.pages, 1):
            page = {"page": number, "text": (source.extract_text(extraction_mode="layout") or "")[:30000] if "/Contents" in source else "", "method": "pdf_text", "warnings": []}
            if not page["text"].strip():
                page["warnings"].append("No embedded text on this page.")
                if tools["ready"] and attempted < max_ocr_pages:
                    attempted += 1
                    try:
                        page.update(recognise_page(path, number, languages))
                    except (subprocess.SubprocessError, OSError, ValueError, KeyError):
                        page["warnings"].append("Local OCR failed or exceeded its resource limit. Retry or supply a text source.")
                else:
                    page["warnings"].append("Local OCR is disabled, required tools/languages are missing, or the per-document OCR page limit was reached.")
            pages.append(page)
    return {"pages": pages, "status": "ready" if pages and all(p["text"].strip() for p in pages) else "needs_ocr"}


def main():
    if resource is not None and sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (100, 100))
    # stdout is a machine JSON pipe. Native Windows may select a legacy encoding
    # for redirected output; ASCII escapes round-trip all Unicode through it.
    print(json.dumps(parse(Path(sys.argv[1]), ocr_mode=os.getenv("OCR_MODE", "auto"), languages=os.getenv("OCR_LANGUAGES", "eng+ara"), max_ocr_pages=int(os.getenv("OCR_MAX_PAGES", "6"))), ensure_ascii=True))


if __name__ == "__main__":
    main()

