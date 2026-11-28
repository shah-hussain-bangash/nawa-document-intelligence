"""Page-aware extraction for synthetic bilingual quotations.

Selectable-text PDF extraction is default; optional OCR fallback requires
Tesseract (eng/ara language data). OCR is never silently enabled.
"""
from decimal import Decimal
from pathlib import Path
import shutil
import subprocess
import tempfile
import re
import unicodedata

import pymupdf

from .core import extract, LABELS


class PDFTextUnavailable(ValueError):
    """Raised when a PDF page has no usable text and OCR was not enabled."""


class OCRUnavailable(RuntimeError):
    """Raised when Tesseract or its requested languages are missing."""


def _check_ocr_languages(languages: str) -> None:
    if not shutil.which("tesseract"):
        raise OCRUnavailable("Tesseract not installed; install tesseract and language data for OCR")
    try:
        proc = subprocess.run(
            ["tesseract", "--list-langs"], text=True, capture_output=True,
            timeout=15, check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise OCRUnavailable(f"Cannot inspect installed Tesseract languages: {exc}") from exc
    installed = set(proc.stdout.splitlines()[1:]) | set(proc.stderr.splitlines()[1:])
    required = set(languages.split("+"))
    missing = required - installed
    if missing:
        raise OCRUnavailable("Missing Tesseract languages: " + ", ".join(sorted(missing)))


def _ocr_page(page, languages: str, page_number: int) -> str:
    # 2x scale (~144 dpi); synthetic samples only. OCR output is untrusted.
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
    with tempfile.TemporaryDirectory(prefix="nawa_ocr_") as temp:
        image = Path(temp) / "page.png"
        image.write_bytes(pix.tobytes("png"))
        try:
            result = subprocess.run(
                ["tesseract", str(image), "stdout", "-l", languages, "--psm", "6"],
                text=True, capture_output=True, timeout=90, check=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise OCRUnavailable(f"OCR failed on page {page_number}: {exc}") from exc
    return result.stdout


def _normalize_pdf_line(line: str) -> str:
    """Normalize common Arabic presentation-form / RTL word-order artifacts.

    Some PDF producers emit Arabic words in visual (reversed word) order.
    Reorder only when that yields a recognized field label; do not treat this
    heuristic as general bidirectional-text repair.
    """
    normalized = unicodedata.normalize("NFKC", line).strip()
    if ":" not in normalized:
        return normalized
    # Some selectable-text PDFs put the Latin currency before an Arabic
    # label in extracted visual order. Recognize only the supported AED case.
    if re.fullmatch(r"AED\s*:\s*العملة", normalized, flags=re.IGNORECASE):
        return "العملة: AED"
    known = {variant.casefold() for vs in LABELS.values() for variant in vs}
    if normalized.split(":", 1)[0].strip().casefold() in known:
        return normalized
    if not re.search(r"[\u0600-\u06ff]", normalized):
        return normalized
    tokens = normalized.split()
    def fix_token(token):
        # Digits in visual-order Arabic PDFs can be reversed, e.g.
        # ٠٠٫٠٠٩ -> ٩٠٠٫٠٠. Only reverse numeral-only tokens.
        if re.fullmatch(r"[0-9٠-٩۰-۹.,٫٬]+", token):
            return token[::-1]
        return token
    candidate = " ".join(fix_token(t) for t in tokens[::-1])
    if candidate.split(":", 1)[0].strip().casefold() in known:
        return candidate
    return normalized


def extract_pdf(path: Path, *, ocr: bool = False, languages: str = "eng+ara",
                max_pages: int | None = None, max_text_chars: int | None = None) -> dict:
    """Extract a fixed-field quotation; attach 1-based page and line evidence.

    OCR fallback applies only to pages without selectable text and only when
    explicitly enabled. Real-world OCR accuracy is not established.
    """
    path = Path(path)
    if ((max_pages is not None and (type(max_pages) is not int or max_pages < 1))
            or (max_text_chars is not None and (type(max_text_chars) is not int or max_text_chars < 1))):
        raise ValueError('Invalid synthetic extraction limit')
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected PDF file: {path}")
    if ocr:
        _check_ocr_languages(languages)
    pieces, locations, ocr_pages, originals = [], [], [], []
    try:
        with pymupdf.open(path) as doc:
            if doc.needs_pass:
                raise ValueError(f"Password-protected PDF not supported: {path.name}")
            if doc.page_count == 0:
                raise PDFTextUnavailable(f"Empty PDF: {path.name}")
            page_count = doc.page_count
            if max_pages is not None and page_count > max_pages:
                raise ValueError('PDF exceeds synthetic page limit')
            total_chars = 0
            for number, page in enumerate(doc, start=1):
                page_text = page.get_text("text", sort=True)
                if not page_text.strip():
                    if not ocr:
                        # Blank intro pages are harmless; only non-text pages
                        # without OCR are skipped (as in Phase 2).
                        continue
                    page_text = _ocr_page(page, languages, number)
                    ocr_pages.append(number)
                total_chars += len(page_text)
                if max_text_chars is not None and total_chars > max_text_chars:
                    raise ValueError('PDF exceeds synthetic extracted-text limit')
                for line_no, line in enumerate(page_text.splitlines(), start=1):
                    pieces.append(_normalize_pdf_line(line))
                    originals.append(line)
                    locations.append((number, line_no))
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise ValueError(f"Cannot read PDF {path.name}: {exc}") from exc

    if not any(line.strip() for line in pieces):
        raise PDFTextUnavailable(
            f"No extractable text in {path.name}; scanned/image-only PDFs need OCR (--ocr)."
        )

    with tempfile.TemporaryDirectory(prefix="nawa_pdf_") as temp:
        text_path = Path(temp) / (path.stem + ".txt")
        text_path.write_text("\n".join(pieces) + "\n", encoding="utf-8")
        try:
            result = extract(text_path)
        except ValueError as exc:
            raise ValueError(f"PDF {path.name}: {exc}") from exc

    result["document"] = path.name
    result["input_type"] = (
        "mixed_text_and_ocr_pdf" if ocr_pages and len(ocr_pages) < page_count
        else "ocr_pdf" if ocr_pages else "text_layer_pdf"
    )
    result["page_count"] = page_count
    result["ocr_pages"] = ocr_pages
    result["evidence_precision"] = "page_and_extracted_line_only"
    for evidence in result["evidence"].values():
        page_num, page_line = locations[evidence["line"] - 1]
        evidence["page"] = page_num
        evidence["page_line"] = page_line
        evidence["method"] = "ocr" if page_num in ocr_pages else "text_layer"
        evidence["raw_extracted_text"] = originals[evidence["line"] - 1]
    return result


def compare_pdfs(paths: list[Path], *, ocr: bool = False, languages: str = "eng+ara") -> dict:
    if len(paths) < 2:
        raise ValueError("At least two quotation PDFs are required")
    quotes = [extract_pdf(Path(p), ocr=ocr, languages=languages) for p in paths]
    valid = [quote for quote in quotes if all(quote["checks"].values())]
    ranked = sorted(valid, key=lambda q: (Decimal(q["total"]), q["supplier"].casefold()))
    return {
        "demo_scope": "Synthetic PDFs; text-layer extraction with optional Tesseract OCR; no LLM or RAG",
        "quotations": quotes,
        "lowest_valid_total": ranked[0]["supplier"] if ranked else None,
        "note": "Price-only ranking for demonstration; not a procurement award recommendation",
    }

