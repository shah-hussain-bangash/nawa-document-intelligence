# Data and Document Requirements

Collection, metadata, lifecycle and sample datasets

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. Collection principle

Use public or synthetic materials initially. A public URL alone does not establish permission for unrestricted reuse; record licence or permitted-use basis. Do not import confidential government, employee, citizen or commercial records without explicit authorisation and an approved processing route.
Maintain a source register. For every collection record owner, origin, allowed use, classification, language, collection date, retention, model-processing permission and any restrictions.

## 2. Initial sample collection

Prepare 30 synthetic suppliers, 10 procurement cases, 20 quotations and 10 public/synthetic policy documents. Include requisitions, RFQ specifications, evaluation checklists and approval matrices. Label synthetic organisations and transactions clearly.
Include Arabic and English materials, text PDFs, scans, tables, inconsistent totals, missing fields, expired quotations and conflicting policy versions. Later add contracts, purchase orders, invoices and delivery receipts only when their workflow is defined. These counts bootstrap development; they do not establish production representativeness.

## 3. Required document metadata

Document: tenant, logical ID, owner, classification, permitted roles/users, source, title and type. Version: immutable ID, content hash, media type, size, original filename, language, publication/effective/expiry dates, superseded version and storage reference.
Processing: pipeline/model versions, state, errors and timestamps. Evidence: version ID, page/section, table cell or text span, original text and extraction status. Unknown dates or permissions must not be silently inferred.

## 4. Structured procurement fields

Supplier: synthetic registration identifier, display name and relevant document references. Quotation: supplier, quotation reference, issue/expiry date, currency and line items. Each item holds description, quantity, unit, unit price, tax basis, delivery cost and stated total.
Store extracted value, reviewed value, evidence location and correction history separately. Use decimal types for financial values. Keep missing, unreadable and inapplicable distinct. Do not retain bank or identity-document fields unless an explicitly defined use requires them.

## 5. Ingestion and annotation standards

Verify file limits and actual parser support. Hash and version originals; reject unsupported or dangerous content with a recoverable explanation. Preserve page numbering and original layout context for tables. Scanned pages need OCR; measure Arabic and English OCR separately.
Annotators label expected fields, acceptable answers, citations, missing evidence and required abstention. A second reviewer checks ambiguous examples. Maintain annotation guidance and disagreement records. Synthetic generation assumptions must be documented.

## 6. Dataset partitioning and quality

Separate development, validation and held-out evaluation by document family/case to reduce duplicate leakage. Keep near-identical templates and supplier cases from crossing splits. For forecasting, split by time and prevent future information entering features.
Track language, source type, scan quality, table complexity and field coverage. Validate totals and date consistency deterministically. Report results by slice and dataset version; do not tune prompts repeatedly on the held-out set.

## 7. Access, storage and lifecycle

Restrict originals, extracted text, embeddings, caches, derived reports and annotations to the same effective access policy. Embeddings are derived data and need governance too. Apply encryption and authorisation to object downloads, not only API records.
Lifecycle: received → validated/quarantined → processing → indexed → superseded/withdrawn → deletion scheduled. A failed document must not become searchable. Permission revocation must remove access promptly, including cached results and citations.

## 8. Retention and deletion contract

Set retention with the data owner before using non-synthetic records. Define active storage, history, audit, legal hold and backup schedules separately. Deleting a document removes or restricts its original, extracted text, chunks, vectors, caches and derived exports according to policy.
Record deletion jobs and verify retrieval no longer returns the material. Backups may expire on a documented schedule; do not promise immediate deletion from all backups. Restoration must reapply deletion and access revocation records.

## 9. Collection readiness checklist

Before a dataset is enabled: ownership/use basis recorded; classification reviewed; processing destination permitted; source metadata complete; samples readable; ground truth reviewed; split leakage checked; access tests passed; retention defined; and deletion exercised.
Deliver a source register, synthetic dataset README, field dictionary, annotation guide, version manifest and evaluation split manifest. The records may be simple CSV/JSON initially, provided schema validation and provenance are preserved.
