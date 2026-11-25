"""Bounded source extraction for minimum supplier-quotation count questions.

This is not a general factual-entailment validator. Recognised minimum-count
statements are rendered from evidence and stored citation metadata, without a
model call. Unknown, conditional, negated or conflicting wording stays visible
as source passages for review. No default count is assumed.
"""
import re

from uae_ai.rag.grounding import normalise


EN_WORDS = {word: number for number, word in enumerate(
    "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split(), 1)}
AR_WORDS = {"واحد": 1, "واحدة": 1, "اثنان": 2, "اثنين": 2, "اثنتان": 2, "اثنتين": 2,
            "ثلاث": 3, "ثلاثة": 3, "اربع": 4, "اربعة": 4, "خمس": 5, "خمسة": 5,
            "ست": 6, "ستة": 6, "سبع": 7, "سبعة": 7, "ثمان": 8, "ثمانية": 8,
            "تسع": 9, "تسعة": 9, "عشر": 10, "عشرة": 10}
QUOTE = r"\b(?:quotations?|quotes?|bids?|offers?)\b|\b(?:عروض|عرضين|عرضان|عرضا|عرض)\b"
REQUIREMENT = r"\b(?:requir\w*|must|minimum|maximum|exactly|least|fewer|عدد|ادنى|الادنى|اقل|الاقل|اكثر|يجب|يلزم|مطلوب\w*|تتطلب|تطلب|تستلزم|يشترط)\b"
UNSAFE = r"\b(?:not|no|never|without|if|when|unless|example|hypothetical|superseded|previous|or|per|above|below|under|over|between|threshold|exceeds?|لا|ليس|ليست|غير|اذا|لو|مثال|سابقة|السابق|او|لكل|تجاوز)\b|\bfor\s+(?:purchases|orders|amounts|each)\b|[?؟]"
EN_COUNT = "|".join(EN_WORDS)
AR_COUNT = "|".join(sorted(AR_WORDS, key=len, reverse=True))
EN_MINIMUM = re.compile(
    rf"\bat least (?P<count>\d+|{EN_COUNT})\s+(?:(?:valid|written|supplier|vendor|competitive|independent)\s+){{0,3}}(?:quotations?|quotes?|bids?|offers?)\b")
AR_MINIMUM = re.compile(
    rf"\b(?:(?P<count>\d+|{AR_COUNT})\s+(?:عروض(?:\s+(?:اسعار|الاسعار))?|عرضا)(?:\s+(?:صالحة|صالح|مستقلة))?"
    rf"|(?P<dual>عرضين|عرضان|عرضا\s+سعر)(?:\s+(?:صالحين|صالحان|مستقلين|سعر))?"
    rf"|(?P<one>عرض\s+واحد)(?:\s+صالح)?)\s+على الاقل\b")


def is_count_question(question):
    text = normalise(question)
    if not re.search(QUOTE, text):
        return False
    # A minimum price is not a minimum count. Compound value/count questions
    # retain the existing route; this extractor only handles the quantity type.
    without_quote_unit = re.sub(r"(?:عرض\s+سعر|عروض\s+(?:الاسعار|اسعار))", "", text)
    if (re.search(r"\b(?:price|cost|amount|value|currency|tax|vat|delivery|validity)\b", text)
        or re.search(r"\b(?:(?:ال|لل|ل)?(?:سعر|مبلغ|قيمة|تكلفة|ضريبة|عملة))\b", without_quote_unit)):
        return False
    english = (re.search(r"\b(?:how many|number of|count of)\b", text)
               and re.search(r"\b(?:requir\w*|need\w*|must|minimum|before|approv\w*|policy|procure\w*)\b", text))
    arabic = (re.search(r"\b(?:كم|عدد|لعدد)\b", text)
              and re.search(r"\b(?:يلزم|يجب|مطلوب\w*|تتطلب|تطلب|موافقة|الموافقة|اعتماد|الاعتماد|دليل|الدليل|سياسة|السياسة|ادنى|الادنى|احتاج)\b", text))
    return bool(english or arabic)


def minimums(text):
    """Return recognised integers and whether a relevant clause needs review."""
    found, uncertain = [], False
    # A question mark remains part of the clause so quoted questions are refused.
    for clause in re.split(r"[.!؛\n]+", normalise(text)):
        if not re.search(QUOTE, clause) or not re.search(REQUIREMENT, clause):
            continue
        if re.search(r"\b(?:each|every)\s+(?:supplier\s+)?quotation\s+must\s+(?:show|contain|include|state)\b", clause):
            continue  # A quotation's fields are not a required number of offers.
        if re.search(UNSAFE, clause):
            uncertain = True
            continue
        values = []
        for match in EN_MINIMUM.finditer(clause):
            value = match["count"]
            values.append(int(value) if value.isdecimal() else EN_WORDS[value])
        for match in AR_MINIMUM.finditer(clause):
            value = match["count"]
            values.append(2 if match["dual"] else 1 if match["one"] else
                          int(value) if value.isdecimal() else AR_WORDS[value])
        if not values or any(not 1 <= value <= 1000 for value in values):
            uncertain = True
        else:
            found.extend(values)
    return found, uncertain


def policy_count_answer(question, evidence, documents):
    if not is_count_question(question):
        return None
    arabic = bool(re.search(r"[\u0621-\u064a]", question))
    available = {doc.id: doc for doc in documents}
    facts, uncertain = [], False
    for index, citation in enumerate(evidence, 1):
        doc = available.get(citation["document_id"])
        if doc is None or doc.status != "ready" or doc.version != citation["version"]:
            uncertain = True
            continue
        if not citation["text"] or not any(
            page["page"] == citation["page"] and citation["text"] in page["text"]
            for page in doc.pages
        ):
            uncertain = True
            continue
        if doc.category not in {"Procurement", "Policy"}:
            continue
        values, unknown = minimums(citation["text"])
        uncertain = uncertain or unknown
        for count in sorted(set(values)):
            facts.append({"minimum": count, "citation": index, "document_id": doc.id,
                          "version": citation["version"], "page": citation["page"]})
    counts = sorted({fact["minimum"] for fact in facts})
    base = {"citations": evidence, "mode": "extractive", "count_facts": facts}
    if uncertain or not counts:
        answer = ("لم أتمكن من التحقق من حد أدنى صريح وغير ملتبس لعدد عروض الأسعار في هذه المقاطع. راجع المصادر المرفقة قبل تحديد المتطلب."
                  if arabic else "I could not verify an explicit, unambiguous minimum quotation count in these passages. Review the attached sources before choosing a requirement.")
        return {**base, "status": "insufficient_evidence", "reason": "policy_count_unverified", "answer": answer}
    if len(counts) > 1:
        # Render source titles from stored citation metadata; never let a model
        # rename a procurement policy as HR, or silently pick a conflicting count.
        details = []
        for fact in facts:
            ref = fact["citation"]
            title = available[fact["document_id"]].title
            details.append(f'{fact["minimum"]} — «{title}» [{ref}]')
        answer = (("تذكر المصادر حدودًا دنيا مختلفة لعدد عروض الأسعار: " if arabic else
                   "The sources state different minimum quotation counts: ")
                  + "; ".join(details) + (". راجع المصادر لتحديد المتطلب المنطبق." if arabic else
                                          ". Review the sources to establish which requirement applies."))
        return {**base, "status": "insufficient_evidence", "reason": "conflicting_policy_counts", "answer": answer}
    references = "".join(f'[{index}]' for index in sorted({fact["citation"] for fact in facts}))
    count = counts[0]
    answer = (f"الحد الأدنى المذكور لعدد عروض الأسعار هو {count} {references}."
              if arabic else f"The cited policies state a minimum of {count} quotations {references}.")
    return {**base, "status": "answered", "reason": "policy_count_verified", "answer": answer}
