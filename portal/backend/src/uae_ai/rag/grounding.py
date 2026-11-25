"""Conservative evidence checks for explicit supplier/contact field questions.

This is a bounded labelled-field gate, not a general semantic entailment model.
Related company names and financial totals are never proof of a requested bank
identifier. Unknown formats are withheld rather than inferred.
"""
from dataclasses import dataclass
import re
import unicodedata
from fastapi import HTTPException


def normalise(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[\u064b-\u065f\u0670\u200e\u200f]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    return text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789"))


def identifier(value):
    value = re.sub(r"[\s-]", "", value).upper()
    return value if re.fullmatch(r"[A-Z0-9]{6,34}", value) and sum(c.isdigit() for c in value) >= 4 else None


def iban(value):
    value = re.sub(r"\s", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", value):
        return None
    expanded = "".join(str(ord(c)-55) if c.isalpha() else c for c in value[4:] + value[:4])
    return value if int(expanded) % 97 == 1 else None


def swift(value):
    value = value.strip().upper()
    return value if re.fullmatch(r"[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?", value) else None


def email(value):
    return value if re.fullmatch(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9.-]*[A-Z0-9])?\.[A-Z]{2,63}", value, re.I) else None


def phone(value):
    if not re.fullmatch(r"\+?[\d ()-]+", value):
        return None
    digits = re.sub(r"\D", "", value)
    return digits if 7 <= len(digits) <= 15 else None


def tax_id(value):
    value = re.sub(r"[ -]", "", value)
    return value if re.fullmatch(r"\d{8,20}", value) else None


@dataclass(frozen=True)
class Field:
    key: str
    english: str
    arabic: str
    query: str
    labels: tuple[str, ...]
    validate: object


FIELDS = (
    Field("account_number", "bank account number", "رقم الحساب البنكي", r"\b(?:bank\s+accounts?(?:\s+(?:numbers?|no\.?))?|accounts?\s+(?:numbers?|no\.?))\b|رقم\s+(?:الحساب|حساب)", ("bank account number", "bank account no", "bank account", "account number", "account no", "رقم الحساب البنكي", "رقم الحساب المصرفي", "رقم الحساب", "رقم حساب البنك"), identifier),
    Field("iban", "IBAN", "رقم الآيبان", r"\biban\b|ايبان", ("iban", "رقم الايبان", "الايبان", "ايبان"), iban),
    Field("swift", "SWIFT/BIC code", "رمز سويفت", r"\b(?:swift|bic)\b|سويفت", ("swift", "swift code", "bic", "bic code", "swift/bic", "swift/bic code", "رمز سويفت", "سويفت"), swift),
    Field("email", "email address", "البريد الإلكتروني", r"\b(?:email|e-mail)\b|البريد\s+الالكتروني|بريد\s+الكتروني", ("email", "e-mail", "email address", "contact email", "supplier email", "البريد الالكتروني", "بريد الكتروني"), email),
    Field("phone", "phone number", "رقم الهاتف", r"\b(?:phone|telephone|mobile|contact\s+number)\b|رقم\s+(?:الهاتف|الجوال|التواصل)|هاتف", ("phone", "phone number", "telephone", "mobile", "contact number", "supplier phone", "رقم الهاتف", "الهاتف", "رقم الجوال"), phone),
    Field("tax_id", "tax registration number", "رقم التسجيل الضريبي", r"\b(?:trn|vat\s+(?:number|registration)|tax\s+(?:number|registration|id))\b|(?:الرقم|رقم)\s+(?:التسجيل\s+)?الضريبي", ("trn", "tax id", "tax number", "tax registration number", "vat number", "vat registration number", "الرقم الضريبي", "رقم التسجيل الضريبي"), tax_id),
)
LABELS = {normalise(label): field for field in FIELDS for label in field.labels}
SUBJECT_LABELS = {normalise(x) for x in ("supplier", "supplier name", "account holder", "account holder name", "beneficiary", "beneficiary name", "اسم المورد", "المورد", "اسم المستفيد", "صاحب الحساب", "المستفيد")}
UNAVAILABLE = re.compile(r"\b(?:not\s+(?:available|provided|supplied|known|applicable)|unknown|redacted|pending|n/?a|none)\b|غير\s+(?:متاح|متوفر|معروف)|محجوب", re.I)


def subject_key(value):
    words = re.findall(r"[^\W_]+", normalise(value), re.UNICODE)
    legal = {"llc", "ltd", "limited", "inc", "pjsc", "fze", "شركة"}
    return " ".join(w for w in words if w not in legal)


def requested_subject(question):
    question = normalise(question).strip(" ?؟.!\n")
    # Explicit possessives and for/of phrases bind the requested supplier.
    possessives = re.findall(r"(.+?)[’']s\s+", question)
    names = []
    for name in possessives:
        name = re.sub(r"^(?:(?:what|which)\s+(?:is|are)\s+|(?:do\s+you\s+have|can\s+you\s+(?:give|show|provide))\s+(?:me\s+)?|(?:please\s+)?(?:show|give|tell|provide)\s+(?:me\s+)?)", "", name)
        if name not in {"what", "who", "where", "it"}: names.append(name)
    if names:
        return subject_key(names[-1]), len(names) > 1
    tail = re.search(r"\b(?:for|of)\s+(.+)$", question)
    if tail:
        name = re.sub(r"^(?:the\s+)?supplier\s+", "", tail[1])
        return subject_key(name), False
    tail = re.search(r"(?:للمورد|للمزود|لشركة|لـ)\s*(.+)$", question)
    if tail:
        return subject_key(tail[1]), False
    tail = re.search(r"(?:البنكي|المصرفي|الايبان|سويفت|الهاتف)\s+ل(.+)$", question)
    if tail:
        return subject_key(tail[1]), False
    # A bare request may put the supplier before the requested field.
    for field in FIELDS:
        match = re.search(field.query, question)
        if match:
            prefix = question[:match.start()].strip()
            prefix = re.sub(r"^(?:what\s+is|what\s+are|what's|please\s+provide|provide|show\s+me|give\s+me|tell\s+me)\s*", "", prefix).strip()
            if prefix and prefix not in {"the", "supplier", "ما", "ما هو", "ما هي", "اعطني"}:
                return subject_key(prefix), False
    return None, False


def request_fields(question):
    text = normalise(question)
    # Policy/process guidance does not require an actual account/contact value.
    process_question = re.search(r"^(?:how\b|why\b|كيف|لماذا)", text.strip()) and re.search(r"\b(?:verify|verified|validate|verification|change|changes|update|updates|manage|approve|protect|handle)\b|التحقق|تغيير|تعديل|حماية|مراجعة", text)
    if process_question or re.search(r"^(?:what\s+(?:is|are)\s+(?:the\s+)?(?:policy|requirements?|procedure|format|process)\b|ما\s+(?:هي\s+)?(?:متطلبات|سياسة|اجراءات))", text.strip()):
        return ()
    return tuple(field for field in FIELDS if re.search(field.query, text))


def _line(text):
    match = re.fullmatch(r"\s*([^:：]{1,70})\s*[:：]\s*(.{1,500})\s*", normalise(text))
    return (match[1].strip(), match[2].strip()) if match else (None, None)


def _unavailable(question, fields, reason="requested_field_not_supported"):
    arabic = bool(re.search(r"[\u0600-\u06ff]", question))
    names = "، ".join(f.arabic for f in fields) if arabic else ", ".join(f.english for f in fields)
    if reason == "conflicting_field_evidence":
        answer = f"تحتوي المصادر المسموح لك الوصول إليها على قيم متعارضة للحقل المطلوب: {names}. حدد المصدر والإصدار الصحيحين واطلب مراجعة بشرية." if arabic else f"The accessible sources contain conflicting values for the requested {names}. Specify the correct source/version and request a human review; I cannot choose a value."
    elif reason == "supplier_not_specified":
        answer = "حدد المورد أو صاحب الحساب المطلوب. لا يمكنني اختيار بيانات مورد آخر." if arabic else "Please specify the supplier or account holder. I cannot choose another supplier's details."
    else:
        answer = f"لم أجد دليلاً كافياً على {names} للمورد أو صاحب الحساب المطلوب في المستندات التي يمكنك الوصول إليها. لا تكفي مطابقة اسم المورد أو مبالغ عروض الأسعار. أضف مصدراً مصرحاً به يتضمن هذه البيانات صراحةً." if arabic else f"I could not find sufficient evidence for the requested {names} for the supplier or account holder in the documents you can access. A matching supplier name or quotation amount is not evidence of that field. Add an authorised source that explicitly provides the requested details."
    return {"status":"insufficient_evidence", "answer":answer, "citations":[], "mode":"extractive", "reason":reason, "requested_fields":[f.key for f in fields]}


def field_evidence(question, documents):
    """Return None for ordinary passage queries; otherwise a gated answer envelope."""
    fields = request_fields(question)
    if not fields:
        return None
    subject, ambiguous = requested_subject(question)
    if ambiguous or not subject:
        return _unavailable(question, fields, "supplier_not_specified")
    if sum(len(page['text']) for doc in documents for page in doc.pages) > 6_000_000:
        raise HTTPException(422, 'The field-check corpus exceeds local capacity. Select a smaller domain.')
    hits = []
    for doc in documents:
        lines = []
        identities = {}
        for page in doc.pages:
            offset = 0
            for original in page["text"].splitlines(keepends=True):
                label, value = _line(original)
                if label in SUBJECT_LABELS and not UNAVAILABLE.search(value):
                    identities[subject_key(value)] = (page, offset, original)
                lines.append((page, offset, original, label, value))
                offset += len(original)
        current = next(iter(identities)) if len(identities) == 1 else None
        for page, offset, original, label, value in lines:
            if label in SUBJECT_LABELS:
                current = subject_key(value) if value and not UNAVAILABLE.search(value) else None
            field = LABELS.get(label)
            if field not in fields or not current or subject and current != subject or UNAVAILABLE.search(value):
                continue
            # Generic account labels require banking context, not a customer ID.
            if field.key == "account_number" and label in {"account number", "account no", "رقم الحساب"} and not re.search(r"\bbank\b|\biban\b|بنك|مصرف|ايبان", normalise(page["text"])):
                continue
            canonical = field.validate(value)
            if canonical:
                hits.append({"field":field.key,"value":canonical,"subject":current,"doc":doc,"page":page,"offset":offset,"identity":identities[current]})
    if not hits or any(not any(h["field"] == field.key for h in hits) for field in fields):
        return _unavailable(question, fields)
    if not subject and len({h["subject"] for h in hits}) > 1:
        return _unavailable(question, fields, "supplier_not_specified")
    if any(len({h["value"] for h in hits if h["field"] == field.key}) > 1 for field in fields):
        return _unavailable(question, fields, "conflicting_field_evidence")
    evidence = []
    seen = {}
    # Deduplicate repeated versions/pages and include identity evidence when it is
    # on a different page from the requested field.
    for hit in hits:
        doc, page = hit["doc"], hit["page"]
        positions = [(page, hit["offset"])]
        if subject and hit["identity"][0]["page"] != page["page"]:
            positions.insert(0, (hit["identity"][0], hit["identity"][1]))
        for source_page, offset in positions:
            key = (doc.id, source_page["page"])
            if any(start <= offset < end for start, end in seen.get(key, [])): continue
            start = max(0, offset-180)
            seen.setdefault(key, []).append((start, start+1300))
            evidence.append({"document_id":doc.id,"version":doc.version,"title":doc.title,"page":source_page["page"],"text":source_page["text"][start:start+1300],"score":1.0,"classification":doc.classification,"retrieval":"labelled_field"})
    if len(evidence) > 4:
        # Select one supporting occurrence per requested field, not repeated
        # company quotations. An overlarge response is withheld conservatively.
        evidence = evidence[:4]
        if any(not any(re.search(r"(?im)^\s*(?:"+"|".join(re.escape(label) for label in field.labels)+r")\s*[:：]", normalise(item["text"])) for item in evidence) for field in fields):
            return _unavailable(question, fields)
    return {"status":"answered", "citations":evidence, "requested_fields":[f.key for f in fields]}
