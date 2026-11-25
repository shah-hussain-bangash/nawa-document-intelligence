"""Escaped, self-contained procurement report for browser print / Save as PDF."""
from html import escape


def render_report(payload, documents):
    def safe(value):
        return escape(str(value if value is not None else "Unknown"), quote=True)

    case = payload["case"]
    quotes = case.get("comparison", {}).get("quotes") or case.get("quotes", [])
    rows = "".join(
        "<tr>" + "".join(f"<td>{safe(value)}</td>" for value in [
            q.get("supplier"), q.get("amount"), q.get("currency"),
            q.get("tax_percent"), q.get("total", "Not calculated"),
            q.get("document_id"),
        ]) + "</tr>" for q in quotes
    )
    sources = "".join(f"<li><strong>{safe(d.title)}</strong> · version {safe(d.version)} · SHA-256: <code>{safe(d.content_hash)}</code></li>" for d in documents)
    approvals = "".join(f"<li>{safe(a.get('status'))} · revision {safe(a.get('revision'))} · reviewer {safe(a.get('decision_by') or 'Pending')} · {safe(a.get('reason', ''))}</li>" for a in payload.get("approvals", []))
    issues = "".join(f"<li>{safe(issue)}</li>" for issue in case.get("comparison", {}).get("issues", []))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{safe(case['reference'])} — Evidence report</title>
<style>body{{font:14px/1.6 system-ui,sans-serif;color:#173e32;max-width:1040px;margin:40px auto;padding:0 24px}}header{{border-bottom:3px solid #b89553;padding-bottom:20px}}h1{{font-size:28px}}h2{{font-size:18px;margin-top:30px}}.notice{{background:#faf4e5;padding:14px;border:1px solid #dac69b}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{text-align:left;border:1px solid #dce5df;padding:10px;overflow-wrap:anywhere}}th{{background:#edf3ee}}li,code{{overflow-wrap:anywhere}}button{{background:#125c46;color:white;border:0;border-radius:6px;padding:12px 18px;cursor:pointer}}small{{color:#526a5d}}@media print{{body{{margin:0;max-width:none;padding:0}}.print-tools{{display:none}}thead{{display:table-header-group}}tr{{break-inside:avoid}}h2{{break-after:avoid}}}}</style></head><body>
<div class="print-tools"><button type="button" onclick="window.print()">Print / Save as PDF</button><p>Choose “Save as PDF” in your browser’s print dialog.</p></div>
<header><small>UAE SOVEREIGN AGENTIC AI · INDEPENDENT LEARNING PLATFORM</small><h1>Procurement evidence report</h1><p>{safe(case['reference'])} · Revision {safe(case['revision'])} · {safe(case['status'])}</p></header>
<p class="notice">SYNTHETIC SANDBOX — SIMULATED OUTCOME. This report is not a purchase award or compliance certification.</p>
<h2>{safe(case['title'])}</h2><p>{safe(case.get('description', ''))}</p><p>Department: {safe(case['department'])} · Budget: {safe(case['currency'])} {safe(case['budget'])} · Due: {safe(case['due_date'])}</p>
<h2>Source-linked quotations</h2><p>Amounts are analyst-entered. Totals appear only when calculated by the comparison workflow. This report does not independently verify the source contents.</p><table><thead><tr><th>Supplier</th><th>Net amount</th><th>Currency</th><th>Tax %</th><th>Total</th><th>Source ID</th></tr></thead><tbody>{rows or '<tr><td colspan="6">No quotations recorded.</td></tr>'}</tbody></table>
<h2>Checks and exceptions</h2><ul>{issues or '<li>No recorded exceptions. This does not imply compliance.</li>'}</ul>
<h2>Evidence versions</h2><ul>{sources or '<li>No evidence attached.</li>'}</ul>
<h2>Review history</h2><ul>{approvals or '<li>No review decision recorded.</li>'}</ul>
<footer><p>Generated: {safe(payload['generated_at'])} · Rules: {safe(case.get('comparison', {}).get('rules_version', 'Not run'))}</p><small>Only sources authorised for the requesting user are included. Retain this report under your data policy.</small></footer></body></html>'''
