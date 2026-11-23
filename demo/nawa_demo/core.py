"""Deterministic bilingual quotation extraction and comparison with line evidence.

Input is UTF-8 text, NOT scanned PDFs. Synthetic data only.
"""
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import json
import re

LABELS = {
    "supplier": ("supplier", "vendor", "المورد", "اسم المورد"),
    "currency": ("currency", "العملة"),
    "subtotal": ("subtotal", "المجموع الفرعي", "الإجمالي قبل الضريبة"),
    "vat_rate": ("vat rate", "vat %", "نسبة ضريبة القيمة المضافة", "نسبة الضريبة"),
    "vat_amount": ("vat amount", "ضريبة القيمة المضافة", "قيمة الضريبة"),
    "total": ("grand total", "total", "الإجمالي شامل الضريبة", "الإجمالي النهائي"),
}
MONEY = Decimal("0.01")


def normalized_number(value: str) -> str:
    """Normalize supported digits and validate separators before removing grouping."""
    mapping = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬", "01234567890123456789.,")
    value = value.strip().translate(mapping)
    suffix = "%" if value.endswith("%") else ""
    if suffix:
        value = value[:-1].strip()
    if not re.fullmatch(r"[+-]?(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?", value):
        raise ValueError("Unsupported or ambiguous number format; review the source")
    return value.replace(",", "") + suffix


def decimal_value(raw: str, field: str) -> Decimal:
    value = normalized_number(raw)
    if value.endswith("%"):
        value = value[:-1].strip()
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid {field}: {raw!r}") from exc
    if not result.is_finite():
        raise ValueError(f"Non-finite {field}")
    return result


def find_fields(text: str) -> dict:
    found = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ":" not in line:
            continue
        label, value = (part.strip() for part in line.split(":", 1))
        key = next((key for key, variants in LABELS.items() if label.casefold() in variants), None)
        if key is None:
            continue
        if key in found:
            raise ValueError(f"Repeated field {key!r} on line {line_number}")
        found[key] = {"value": value, "line": line_number, "source_text": line}
    missing = set(LABELS) - set(found)
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(sorted(missing)))
    return found


def extract(path: Path) -> dict:
    path = Path(path)
    fields = find_fields(path.read_text(encoding="utf-8"))
    values = {key: evidence["value"] for key, evidence in fields.items()}
    for key in ("subtotal", "vat_rate", "vat_amount", "total"):
        values[key] = decimal_value(values[key], key)
    if not values["supplier"] or not values["currency"]:
        raise ValueError("Supplier and currency must not be empty")
    if values["currency"].upper() != "AED":
        raise ValueError("This demo supports AED quotations only")
    if any(values[k] < 0 for k in ("subtotal", "vat_rate", "vat_amount", "total")):
        raise ValueError("Negative financial values are unsupported")
    if values["vat_rate"] > 100:
        raise ValueError("VAT rate cannot exceed 100 percent")
    expected_vat = (values["subtotal"] * values["vat_rate"] / 100).quantize(MONEY, rounding=ROUND_HALF_UP)
    expected_total = (values["subtotal"] + values["vat_amount"]).quantize(MONEY, rounding=ROUND_HALF_UP)
    checks = {
        "vat_matches_rate": values["vat_amount"] == expected_vat,
        "total_matches_components": values["total"] == expected_total,
    }
    return {
        "document": path.name,
        "supplier": values["supplier"],
        "currency": "AED",
        "subtotal": str(values["subtotal"]),
        "vat_rate_percent": str(values["vat_rate"]),
        "vat_amount": str(values["vat_amount"]),
        "total": str(values["total"]),
        "expected_vat": str(expected_vat),
        "expected_total": str(expected_total),
        "checks": checks,
        "evidence": fields,
    }


def compare(paths: list[Path]) -> dict:
    if len(paths) < 2:
        raise ValueError("At least two quotations are required")
    quotes = [extract(Path(path)) for path in paths]
    valid = [q for q in quotes if all(q["checks"].values())]
    ranked = sorted(valid, key=lambda q: (Decimal(q["total"]), q["supplier"].casefold()))
    return {
        "demo_scope": "Synthetic UTF-8 text files; rules-based parser, not OCR or RAG",
        "quotations": quotes,
        "lowest_valid_total": (ranked[0]["supplier"] if ranked else None),
        "note": "Price-only ranking for demonstration; not a procurement award recommendation",
    }


def write_json(report: dict, output: Path | None = None) -> str:
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if output is not None:
        Path(output).write_text(rendered + "\n", encoding="utf-8")
    return rendered
