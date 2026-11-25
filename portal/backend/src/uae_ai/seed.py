"""Idempotent synthetic fixtures. Never seeds in production."""
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select
from uae_ai.db import Approval, Audit, Case, Document, Run, Tenant, Ticket, User, now
from uae_ai.graphs.procurement import compare_quotes, evidence_digest

ROLES = {"analyst": "Amira Al Mansoori", "reviewer": "Omar Al Nuaimi", "requester": "Sara Ahmed", "auditor": "Khalid Hassan", "admin": "Noor Al Falasi"}
POLICIES = [
    ("Procurement operating framework", "Procurement", "en", "Synthetic procurement policy, version 1. Competitive procurement requires at least two valid supplier quotations. Each quotation must show supplier name, currency, net amount, tax, delivery terms and validity date. A human reviewer must approve the comparison before a simulated outcome. No actual payment or award is executed by this learning platform."),
    ("Supplier due diligence checklist", "Procurement", "en", "Synthetic supplier onboarding guidance. Check registration validity, authorised contacts, quotation validity and source-linked price evidence. Missing or expired supplier documents require information from the analyst. Do not infer eligibility from a model confidence score."),
    ("Review and approval authority", "Policy", "en", "Synthetic approval policy. Reviewers must be independent from the person preparing the case. Approval binds the current case revision, evidence versions and comparison. Changed quotations invalidate pending approval. The reviewer can approve, reject or request changes with a recorded reason."),
    ("Data handling and retention", "Policy", "en", "Synthetic data policy. This workspace contains synthetic demonstration records. Document access is scoped by tenant and role. Uploaded confidential data must not be sent to unapproved external models. Deletion removes active passages and source access. Backup retention must be separately governed."),
    ("Annual leave and employee guidance", "HR", "en", "Synthetic HR policy for a fictional organisation. Employees submit annual leave requests to their line manager for review. This example provides 25 working days of annual leave per year. This is not UAE legal advice or an official employment policy. HR questions requiring personal records must be referred to an authorised person."),
    ("Service desk escalation playbook", "Service desk", "en", "Synthetic service desk guidance. Access requests require a manager review and least-privilege checks. A security incident must be escalated to the security owner immediately. IT support tickets can be classified as normal, high or urgent. Sensitive responses require human review."),
    ("دليل المشتريات التجريبي", "Procurement", "ar", "سياسة تجريبية للمشتريات. يجب إرفاق عرضين صالحين على الأقل مع اسم المورد والعملة والسعر والضريبة وتاريخ الصلاحية. تتطلب الموافقة مراجعة بشرية مستقلة. تعديل المستندات يلغي الموافقة المعلقة. هذه بيانات اصطناعية وليست سياسة حكومية رسمية."),
    ("دليل الموارد البشرية", "HR", "ar", "سياسة موارد بشرية تجريبية لمؤسسة افتراضية. يقدم الموظف طلب الإجازة السنوية إلى المدير للمراجعة. يمنح هذا المثال خمسة وعشرين يوم عمل سنوياً. هذا النص ليس استشارة قانونية أو سياسة رسمية. تتطلب القرارات الوظيفية مراجعة بشرية."),
    ("Information access controls", "Policy", "en", "Synthetic access policy. Analyst and reviewer roles access their tenant's permitted evidence. Auditors can inspect permitted records but cannot approve cases. Tenant administration does not grant unrestricted cross-tenant access. Sessions expire and revoked memberships cannot continue queued work."),
    ("Document evidence standards", "Policy", "en", "Synthetic document standards. Evidence must retain its original source, document version and page references. Scanned documents require OCR before text retrieval. If a source is unreadable or evidence is missing, the assistant must abstain rather than invent a response."),
]


def seed(db, settings):
    if db.scalar(select(Tenant).limit(1)):
        return
    today = date.today()
    for tenant_id, name in [("operations", "Emirates Operations"), ("research", "Research Lab")]:
        db.add(Tenant(id=tenant_id, name=name))
        users = {}
        for role, full_name in ROLES.items():
            user = User(id=f"{tenant_id}-{role}", tenant_id=tenant_id, name=full_name, email=f"{role}@{tenant_id}.example", role=role, active=True, preferences={"language": "en", "digest": True})
            db.add(user)
            users[role] = user
        db.flush()
        documents = []
        for index, (title, category, language, content) in enumerate(POLICIES):
            doc_id = f"{tenant_id}-policy-{index+1}"
            path = settings.data_dir / "uploads" / f"{doc_id}.txt"
            path.write_text(content, encoding="utf-8")
            doc = Document(id=doc_id, tenant_id=tenant_id, created_by=users["analyst"].id, title=title, filename=title + ".txt", category=category, classification="synthetic", allowed_roles=list(ROLES), language=language, content_hash=hashlib.sha256(content.encode()).hexdigest(), pages=[{"page": 1, "text": content}], size=len(content.encode()), source="Synthetic demonstration policy", status="ready", version=1)
            db.add(doc)
            documents.append(doc)
        titles = ["Cloud infrastructure renewal", "Employee learning platform", "Network security assessment", "Office workspace equipment", "Arabic document processing", "Service desk automation", "Secure storage expansion", "Accessibility review", "Analytics dashboard services", "Developer workstation refresh"]
        departments = ["Digital Services", "Human Capital", "Cybersecurity", "Corporate Services", "Digital Services", "IT Operations", "IT Operations", "Digital Services", "Strategy & Planning", "Corporate Services"]
        states = ["awaiting_review", "awaiting_review", "draft", "needs_information", "draft", "approved_simulation", "draft", "approved_simulation", "rejected", "draft"]
        suppliers = ["Falcon Digital", "Atlas Technology", "Palm Systems", "Horizon Solutions", "Crescent Cloud", "Oasis Technologies"]
        for index, title in enumerate(titles):
            quotation_docs = []
            quotes = []
            budget = Decimal(str([240000, 125000, 95000, 68000, 180000, 85000, 155000, 45000, 92000, 78000][index]))
            for j in range(2):
                supplier = suppliers[(index+j) % len(suppliers)]
                amount = (budget * Decimal(str(0.72 + j * 0.09))).quantize(Decimal("0.01"))
                content = f"SYNTHETIC QUOTATION\nSupplier: {supplier}\nProject: {title}\nNet amount: {amount} AED\nTax: 5%\nDelivery: {14 + j * 7} days\nValid until: {today + timedelta(days=30)}\nDelivery included in net amount. Fictional learning sample, not a real offer."
                doc_id = f"{tenant_id}-quote-{index}-{j}"
                (settings.data_dir / "uploads" / f"{doc_id}.txt").write_text(content)
                doc = Document(id=doc_id, tenant_id=tenant_id, created_by=users["analyst"].id, title=f"{supplier} · {title}", filename=f"quotation-{index+1}-{j+1}.txt", category="Quotation", classification="synthetic", allowed_roles=list(ROLES), language="en", status="ready", version=1, content_hash=hashlib.sha256(content.encode()).hexdigest(), pages=[{"page": 1, "text": content}], size=len(content), source="Synthetic supplier quotation")
                db.add(doc)
                quotation_docs.append(doc_id)
                quotes.append({"supplier": supplier, "amount": str(amount), "currency": "AED", "delivery_days": 14 + j * 7, "valid_until": (today+timedelta(days=30)).isoformat(), "document_id": doc_id, "tax_percent": "5"})
            case = Case(id=f"{tenant_id}-case-{index+1}", tenant_id=tenant_id, reference=f"PR-{today.year}-{1001+index}", title=title, description="Synthetic procurement case for the independent Nawa demonstration workspace. Compare evidence and validate the supplied quotation amounts before reviewing.", department=departments[index], created_by=users["analyst"].id, budget=budget, due_date=(today+timedelta(days=index+2)).isoformat(), priority="High" if index in [0,2,4] else "Normal", status=states[index], revision=1, currency="AED", document_ids=[documents[0].id, *quotation_docs], quotes=quotes, created_at=(today-timedelta(days=index+1)).isoformat()+"T09:00:00+00:00")
            db.add(case)
            db.flush()
            if states[index] in {"awaiting_review", "approved_simulation", "rejected"}:
                case.comparison = compare_quotes(case)
                snapshot = evidence_digest(db, case)
                run = Run(tenant_id=tenant_id, case_id=case.id, actor_id=users["analyst"].id, request_key=f"seed-{case.id}", fingerprint=snapshot, revision=1, status=states[index], snapshot=snapshot, steps=[{"name": name, "status": "completed", "detail": "Prepared synthetic sample"} for name in ["Intake validated", "Deterministic validation", "Evidence-linked comparison"]])
                db.add(run)
                db.flush()
                pending = states[index] == "awaiting_review"
                db.add(Approval(tenant_id=tenant_id, case_id=case.id, run_id=run.id, revision=1, snapshot=snapshot, requested_by=users["analyst"].id, status="pending" if pending else ("approved" if states[index]=="approved_simulation" else "rejected"), decision_by=None if pending else users["reviewer"].id, reason=None if pending else "Synthetic sample decision for demonstration.", decided_at=None if pending else now()))
            db.add(Audit(tenant_id=tenant_id, actor=users["analyst"].name, role="analyst", action="Sample case prepared", resource=case.reference, details={"synthetic": True, "state": states[index]}, created_at=case.created_at))
        for index, (title, cat, priority, status) in enumerate([
            ("Access to procurement evidence library", "Access request", "High", "Open"),
            ("Arabic report export formatting", "IT support", "Normal", "In progress"),
            ("New employee onboarding guidance", "HR enquiry", "Normal", "Open"),
            ("Meeting room display connection", "Facilities", "Normal", "Resolved"),
            ("Review workspace permission", "Access request", "High", "Open"),
            ("Document upload assistance", "IT support", "Normal", "Resolved"),
        ]):
            db.add(Ticket(tenant_id=tenant_id, title=title, category=cat, priority=priority, status=status, created_by="Synthetic service requester"))
    db.commit()

