"""Evaluate synthetic scanned quotations with the local PDF OCR demo."""
import argparse
import io
import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pymupdf
from PIL import Image, ImageDraw, ImageFont

from nawa_demo.pdf_ingest import extract_pdf

ENGLISH_LABELS = ("Supplier", "Currency", "Subtotal", "VAT rate", "VAT amount", "Grand total")
ARABIC_LABELS = ("اسم المورد", "العملة", "المجموع الفرعي", "نسبة الضريبة", "قيمة الضريبة", "الإجمالي شامل الضريبة")
OUTPUT_FIELDS = ("supplier", "currency", "subtotal", "vat_rate_percent", "vat_amount", "total")
EVIDENCE_FIELDS = ("supplier", "currency", "subtotal", "vat_rate", "vat_amount", "total")

def create_scan(path, font_path, language, mismatch):
    arabic_supplier = "شركة المثال للتوريدات"
    labels = {
        "English": ENGLISH_LABELS,
        "Arabic": ARABIC_LABELS,
        "Mixed": ARABIC_LABELS[:3] + ENGLISH_LABELS[3:],
    }[language]
    supplier = "Example Supplies" if language == "English" else arabic_supplier
    values = (supplier, "AED", "900.00", "5", "40.00" if mismatch else "45.00", "940.00" if mismatch else "945.00")
    image = Image.new("RGB", (1240, 1000), "white")
    canvas = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, 43, layout_engine=ImageFont.Layout.RAQM)
    for index, (label, value) in enumerate(zip(labels, values)):
        rtl = label in ARABIC_LABELS
        canvas.text((1150 if rtl else 90, 85 + 125 * index), f"{label}: {value}",
                    font=font, fill="black", anchor="rt" if rtl else "lt",
                    direction="rtl" if rtl else "ltr")
    png = io.BytesIO()
    image.save(png, format="PNG")
    with pymupdf.open() as pdf:
        page = pdf.new_page(width=620, height=500)
        page.insert_image(page.rect, stream=png.getvalue())
        pdf.save(path)
    return values

def evaluate(path, expected, mismatch):
    start = perf_counter()
    try:
        result = extract_pdf(path, ocr=True, languages="eng+ara")
    except ValueError as exc:
        return {"fields_correct": 0, "ocr_page_refs": 0, "vat_outcome": "not reached",
                "seconds": round(perf_counter() - start, 2), "error": str(exc)}
    fields = [
        result[key] == value if index < 2 else Decimal(result[key]) == Decimal(value)
        for index, (key, value) in enumerate(zip(OUTPUT_FIELDS, expected))
    ]
    refs = sum(result["evidence"][key]["page"] == 1 and result["evidence"][key]["method"] == "ocr"
               and result["evidence"][key]["page_line"] > 0 and bool(result["evidence"][key]["raw_extracted_text"].strip())
               for key in EVIDENCE_FIELDS)
    vat = result["checks"]["vat_matches_rate"]
    return {"fields_correct": sum(fields), "ocr_page_refs": refs,
            "vat_outcome": "correct" if vat == (not mismatch) else "wrong",
            "seconds": round(perf_counter() - start, 2)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("font", help="Path to a font covering Arabic and Latin, such as DejaVu Sans")
    args = parser.parse_args()
    results = []
    with TemporaryDirectory(prefix="nawa_scan_eval_") as temp_dir:
        for language in ("English", "Arabic", "Mixed"):
            for mismatch in (False, True):
                path = Path(temp_dir) / f"{language}_{'wrong_vat' if mismatch else 'valid'}.pdf"
                expected = create_scan(path, args.font, language, mismatch)
                results.append({"fixture": path.stem, **evaluate(path, expected, mismatch)})
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
