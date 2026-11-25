"""Conservative labelled quotation drafts. No model calls or document instructions."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import unicodedata

VERSION = "labelled-quotation-v1"
LABELS = {
    "supplier": ["supplier", "supplier name", "المورد", "اسم المورد"],
    "amount": ["net amount", "net price", "المبلغ الصافي", "صافي المبلغ"],
    "currency": ["currency", "العملة"],
    "tax_percent": ["tax", "tax percentage", "vat", "الضريبة", "نسبة الضريبة"],
    "delivery_days": ["delivery", "delivery days", "مدة التسليم", "التسليم"],
    "valid_until": ["valid until", "validity date", "صالح حتى", "تاريخ الصلاحية"],
}
KEYS = {label.casefold(): key for key, labels in LABELS.items() for label in labels}
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
CURRENCY = {"AED": "AED", "USD": "USD", "EUR": "EUR", "درهم": "AED", "دولار": "USD", "يورو": "EUR"}


def number(raw, *, tax=False):
    raw = raw.strip()
    # Comma is allowed only as a full thousands grouping, never guessed as decimal.
    if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?", raw):
        return None
    try:
        value = Decimal(raw.replace(",", ""))
    except InvalidOperation:
        return None
    if not (Decimal("0") <= value <= (100 if tax else 100_000_000)) or not tax and value == 0:
        return None
    return format(value, ".2f")


def extract_quotation(doc):
    candidates = {key: [] for key in LABELS}

    def add(key, value, page, excerpt):
        candidates[key].append({"value": value, "page": page, "excerpt": excerpt[:500]})

    for page in doc.pages:
        for original in page.get("text", "")[:200_000].splitlines()[:4000]:
            line = unicodedata.normalize("NFKC", original).translate(DIGITS).strip()
            match = re.fullmatch(r"([^:：]{1,50})\s*[:：]\s*(.{1,500})", line)
            if not match:
                continue
            key = KEYS.get(match[1].strip().casefold())
            if not key:
                continue
            raw = match[2].strip()
            value = None
            if key == "supplier":
                value = raw if 2 <= len(raw) <= 120 else None
            elif key == "currency":
                value = CURRENCY.get(raw.upper())
            elif key == "amount":
                money = re.fullmatch(r"(.+?)\s+(AED|USD|EUR|درهم|دولار|يورو)", raw, re.I)
                if money:
                    value = number(money[1])
                    add("currency", CURRENCY[money[2].upper()], page["page"], original)
                else:
                    value = number(raw)
            elif key == "tax_percent":
                tax = re.fullmatch(r"(.+?)\s*[%٪]", raw)
                value = number(tax[1], tax=True) if tax else None
            elif key == "delivery_days":
                delivery = re.fullmatch(r"(\d{1,3})\s*(?:days?|يوم|أيام|يوما|يوماً)", raw, re.I)
                if delivery and int(delivery[1]) <= 730:
                    value = str(int(delivery[1]))
            elif key == "valid_until" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                try:
                    value = date.fromisoformat(raw).isoformat()
                except ValueError:
                    pass
            add(key, value, page["page"], original)

    fields = {}
    for key, values in candidates.items():
        distinct = {item["value"] for item in values}
        status = "missing" if not values else "invalid" if distinct == {None} else "ambiguous" if len(distinct) != 1 else "found"
        fields[key] = {"value": next(iter(distinct)) if status == "found" else None, "status": status, "evidence": values[:5]}
    return {
        "extractor_version": VERSION,
        "source": {"document_id": doc.id, "title": doc.title, "version": doc.version, "sha256": doc.content_hash},
        "fields": fields,
        "requires_review": True,
        "notice": "Draft only. Review every field against the original source, especially OCR text. Missing, invalid or conflicting values require manual entry. Labelled fields only; arbitrary table semantics are not inferred.",
    }
