import hashlib
import json
import time
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import TypedDict
from langgraph.graph import StateGraph, END
from sqlalchemy import update
from uae_ai.db import Document, Run


RULE_VERSION = "procurement-checklist-v1"


def evidence_digest(db, case):
    sources = []
    for doc_id in sorted(case.document_ids):
        doc = db.get(Document, doc_id)
        sources.append({"id": doc_id, "hash": doc.content_hash if doc else None, "version": doc.version if doc else None, "status": doc.status if doc else "missing"})
    payload = {"tenant": case.tenant_id, "case": case.id, "revision": case.revision, "quotes": case.quotes, "sources": sources, "budget": str(case.budget), "currency": case.currency, "rules": RULE_VERSION}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def compare_quotes(case):
    issues = []
    quotes = []
    if len(case.quotes) < 2:
        issues.append("At least two source-linked quotations are required.")
    if not case.document_ids:
        issues.append("Attach approved source evidence before requesting review.")
    for index, quote in enumerate(case.quotes):
        amount = Decimal(str(quote["amount"]))
        tax = (amount * Decimal(str(quote.get("tax_percent", "5"))) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = amount + tax
        quote_issues = []
        if quote["currency"] != case.currency:
            quote_issues.append("Currency does not match the case; no exchange rate is assumed.")
        if date.fromisoformat(quote["valid_until"]) < date.today():
            quote_issues.append("Quotation has expired.")
        if quote["document_id"] not in case.document_ids:
            quote_issues.append("Quotation is not linked to attached evidence.")
        if total > case.budget:
            quote_issues.append("Tax-inclusive total exceeds the case budget.")
        issues.extend(f'{quote["supplier"]}: {issue}' for issue in quote_issues)
        quotes.append({**quote, "tax": str(tax), "total": str(total), "issues": quote_issues, "position": index + 1})
    # Quotes remain in submission order: the model does not choose a winner.
    return {"quotes": quotes, "issues": issues, "rules_version": RULE_VERSION, "calculation": "Net amount + supplied tax percentage; delivery assumed included in net quotation. Human verification required.", "simulated": True}


class State(TypedDict):
    case_id: str
    findings: dict


def execute_graph(db, case, run):
    token = run.execution_token
    def record(name, detail):
        steps = [*run.steps, {"name": name, "status": "completed", "detail": detail}]
        saved = db.execute(update(Run).where(Run.id == run.id, Run.execution_token == token, Run.status == 'processing').values(steps=steps, execution_until=int(time.time())+60))
        if not saved.rowcount:
            db.rollback()
            raise RuntimeError('This deterministic run no longer owns its execution lease')
        db.commit()

    def intake(state):
        record("Intake validated", f"Case revision {case.revision} and {len(case.document_ids)} evidence references")
        return state

    def rules(state):
        result = compare_quotes(case)
        record("Deterministic validation", f'{len(result["quotes"])} quotations checked; {len(result["issues"])} findings')
        return {**state, "findings": result}

    def draft(state):
        record("Evidence-linked comparison", "Comparison prepared for human review; no external action executed")
        return state

    builder = StateGraph(State)
    builder.add_node("intake", intake)
    builder.add_node("rules", rules)
    builder.add_node("draft", draft)
    builder.set_entry_point("intake")
    builder.add_edge("intake", "rules")
    builder.add_edge("rules", "draft")
    builder.add_edge("draft", END)
    return builder.compile().invoke({"case_id": case.id, "findings": {}}, config={"recursion_limit": 8})["findings"]

