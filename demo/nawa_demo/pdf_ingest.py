"""Page-aware extraction for text-layer supplier quotation PDFs.

Requires PyMuPDF. No OCR. Existing rules-based core handles validation.
"""
from decimal import Decimal
from pathlib import Path
import tempfile

import fitz

from .core import extract


class PDFTextUnavailable(ValueError):
    """Raised for scanned/image-only PDFs or PDFs without extractable text."""


def extract_pdf(path: Path) -> dict:
    """Parse a text-based PDF, returning original page/line evidence per field.

    Page numbers and page-line values are 1-based. Bounding boxes are not claimed.
    """
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected PDF file: {path}")

    pieces = []
    locations = []
    try:
        with fitz.open(path) as doc:
            if doc.needs_pass:
                raise ValueError(f"Password-protected PDF not supported: {path.name}")
            if doc.page_count == 0:
                raise PDFTextUnavailable(f"Empty PDF: {path.name}")
            for number, page in enumerate(doc, start=1):
                text = page.get_text("text", sort=True)
                for line_no, line in enumerate(text.splitlines(), start=1):
                    pieces.append(line)
                    locations.append((number, line_no))
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ValueError(f"Cannot read PDF {path.name}: {exc}") from exc

    if not any(line.strip() for line in pieces):
        raise PDFTextUnavailable(
            f"No extractable text in {path.name}; scanned/image-only PDFs need OCR (not implemented)."
        )

    # The legacy parser accepts a UTF-8 text path. Feed its full extracted text
    # to that parser without modifying the financial validation logic.
    with tempfile.TemporaryDirectory(prefix="nawa_pdf_") as temp:
        text_path = Path(temp) / (path.stem + ".txt")
        text_path.write_text("\n".join(pieces) + "\n", encoding="utf-8")
        try:
            result = extract(text_path)
        except ValueError as exc:
            raise ValueError(f"PDF {path.name}: {exc}") from exc

    result["document"] = path.name
    result["input_type"] = "text_layer_pdf"
    result["page_count"] = number
    result["evidence_precision"] = "page_and_extracted_line_only"
    for evidence in result["evidence"].values():
        flat_line = evidence["line"]
        page_num, page_line = locations[flat_line - 1]
        evidence["page"] = page_num
        evidence["page_line"] = page_line
        # Keep existing line as a flattened extracted-text line number.
    return result


def compare_pdfs(paths: list[Path]) -> dict:
    if len(paths) < 2:
        raise ValueError("At least two quotation PDFs are required")
    quotes = [extract_pdf(Path(p)) for p in paths]
    valid = [quote for quote in quotes if all(quote["checks"].values())]
    ranked = sorted(valid, key=lambda q: (Decimal(q["total"]), q["supplier"].casefold()))
    return {
        "demo_scope": "Synthetic text-layer PDFs; rules-based parser; no OCR, LLM or RAG",
        "quotations": quotes,
        "lowest_valid_total": ranked[0]["supplier"] if ranked else None,
        "note": "Price-only ranking for demonstration; not a procurement award recommendation",
    }
