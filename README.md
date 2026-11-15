# NAWA | Bilingual Document Intelligence

**Enterprise Document AI • Arabic & English OCR • Evidence-Linked Extraction • RAG • Human-in-the-Loop Review**

NAWA is an enterprise document intelligence project designed to help procurement teams process and compare Arabic and English supplier quotations.

The system combines document processing, structured information extraction, evidence-linked retrieval, deterministic financial comparisons, and human review to make procurement decisions more traceable.

**Project type:** Enterprise AI engineering portfolio  
**Domain:** Procurement and supplier quotation intelligence  
**Development role:** Sole developer  
**Data:** Synthetic documents for portfolio demonstrations  
**Status:** Development project; production readiness not established

---

## 1. Business Problem

Supplier quotation reviews often involve scanned PDFs, mixed Arabic and English content, inconsistent document layouts, and manually checked financial information.

These challenges can create:

- Time-consuming document review.
- Errors in extracted totals, VAT, and currency values.
- Difficulty tracing extracted information to its source.
- Inconsistent comparisons between supplier quotations.
- Limited auditability of manual corrections.

**NAWA addresses these challenges through document intelligence, evidence-linked extraction, and controlled human review.**

## 2. Solution Overview

The NAWA solution is organized around six capabilities:

| Capability | Purpose |
|---|---|
| Document ingestion | Accept and process supplier quotation documents |
| Bilingual OCR | Extract content from Arabic and English documents |
| Structured extraction | Identify supplier details, monetary values, and other quotation fields |
| Evidence-linked retrieval | Connect extracted information to source documents and pages |
| Quotation comparison | Identify discrepancies, including VAT and total differences |
| Human review | Allow reviewers to inspect evidence and correct disputed values |

The architecture also addresses document permissions, processing workflows, auditability, and cloud operations.

Implementation and verification status must be assessed separately for each capability.

## 3. System Architecture

NAWA's architecture documentation describes the following logical flow:

**Document Upload → Validation → OCR & Extraction → Structured Data & Evidence → Retrieval & Comparison → Human Review**

Supporting concerns include:

- Identity and access control.
- Document and version management.
- Processing jobs and failure handling.
- Database persistence.
- Retrieval and citation integrity.
- Audit records.
- Cloud deployment and monitoring.

See [System Architecture](docs/02-system-architecture/NAWA_System_Architecture.pdf) and [Architecture Decisions](docs/02-system-architecture/NAWA_Architecture_Decisions.pdf).

## 4. Document AI and RAG

NAWA explores a document-processing architecture that combines OCR, structured field extraction, and evidence-linked retrieval.

The retrieval design includes a lexical BM25 baseline and optional embedding-based retrieval and fusion.

Important engineering considerations include:

- Arabic and English document normalization.
- Page-linked source references.
- Extraction confidence and missing-field handling.
- Document version consistency.
- Permission-aware retrieval.
- Human verification of uncertain results.

See [Document AI & RAG](docs/03-document-ai-rag/NAWA_Document_AI_and_RAG.pdf).

## 5. Human-in-the-Loop Review

The review workflow is designed to preserve human accountability.

A reviewer should be able to:

1. Inspect a supplier quotation.
2. Review an extracted financial value.
3. Follow the evidence reference to its original page.
4. Identify a discrepancy in VAT or totals.
5. Record a correction or review decision.
6. Recalculate or refresh the affected comparison.
7. Preserve a traceable review history.

See [Review Workflow](docs/03-document-ai-rag/NAWA_Review_Workflow.pdf).

## 6. Technology and Engineering

The project documentation and reported development environment reference the following technologies:

| Area | Technology or approach |
|---|---|
| Application | Web interface, backend APIs, processing workflows |
| Database | PostgreSQL |
| Supporting services | Redis |
| Deployment | Docker and AWS EC2 development workspace |
| HTTPS ingress | Caddy |
| Authentication | AWS Cognito with Google sign-in in the reported AWS environment |
| Local identity validation | Keycloak with PKCE |
| Document intelligence | OCR, structured extraction, evidence-linked retrieval |
| Search design | BM25 baseline with optional vector retrieval |

**Note:** This table describes the reported environment and architecture. It does not independently verify that every component is currently running or publicly reproducible.

## 7. Testing and Evaluation

The project résumé reports:

- 123 passing local automated tests.
- Local backup and restore validation.
- Cognito sign-in in the AWS development workspace.

These are previously reported observations, not independently reproduced results in this repository.

### Evaluation work remaining

The following results require published benchmark evidence:

- Arabic and English OCR character error rates.
- Structured extraction accuracy.
- Retrieval Recall@5.
- Citation correctness.
- Permission-isolation test outcomes.
- Processing latency and reliability.
- Cloud recovery measurements.

The proposed bilingual evaluation pilot uses 60 synthetic or permissioned documents, with balanced Arabic, English, and mixed-language groups.

See [Evaluation Plan](docs/05-testing-evaluation/NAWA_Arabic_and_English_Evaluation_Plan.pdf) and [Evaluation Report](docs/05-testing-evaluation/NAWA_Evaluation_Report.pdf).

## 8. Security and Governance

NAWA's security design addresses:

- Authentication and role-based access.
- Tenant and document authorization boundaries.
- Source evidence permissions.
- Audit logging.
- Secure handling of uploaded documents.
- Data retention and deletion.
- Human oversight of uncertain AI outputs.

These are documented design considerations. Control-level implementation and test evidence must be linked before claiming verified enforcement.

See [Security Design](docs/04-security-governance/NAWA_Security_Design.pdf) and [AI Governance & Risk Assessment](docs/04-security-governance/NAWA_AI_Governance_and_Risk_Assessment.pdf).

## 9. Cloud and Operations

The reported AWS development environment includes containerized application services, HTTPS ingress, database infrastructure, and identity integration.

The operations documentation covers proposed procedures for:

- Deployment and rollback.
- Monitoring and alerting.
- Backup and restoration.
- Incident handling.
- Disaster recovery.
- Production readiness assessment.

A documented procedure is not equivalent to a completed operational test.

See [Cloud Operations](docs/06-cloud-devops/NAWA_Cloud_Operations.pdf).

## 10. Technical Documentation

### Business and requirements

- [Project Vision & Scope](docs/01-business-requirements/NAWA_Project_Vision_and_Scope.pdf)
- [Business Requirements Document](docs/01-business-requirements/NAWA_BRD_Download_Fixed.pdf)
- [Software Requirements Specification](docs/01-business-requirements/NAWA_SRS_Download_Fixed.pdf)

### Architecture and API design

- [System Architecture](docs/02-system-architecture/NAWA_System_Architecture.pdf)
- [Architecture Decisions](docs/02-system-architecture/NAWA_Architecture_Decisions.pdf)
- [Database Architecture & ERD](docs/02-system-architecture/NAWA_Database_Architecture_and_ERD.pdf)
- [API Design & Integration Specification](docs/02-system-architecture/NAWA_API_Design_and_Integration_Specification.pdf)

### Document AI and evaluation

- [Document AI & RAG](docs/03-document-ai-rag/NAWA_Document_AI_and_RAG.pdf)
- [OCR & Bilingual Extraction Specification](docs/03-document-ai-rag/NAWA_OCR_and_Bilingual_Extraction_Specification.pdf)
- [Arabic & English Evaluation Plan](docs/05-testing-evaluation/NAWA_Arabic_and_English_Evaluation_Plan.pdf)
- [Evaluation Report](docs/05-testing-evaluation/NAWA_Evaluation_Report.pdf)
- [Testing & Quality Assurance Strategy](docs/05-testing-evaluation/NAWA_Testing_and_Quality_Assurance_Strategy.pdf)

### Security and governance

- [Security Design](docs/04-security-governance/NAWA_Security_Design.pdf)
- [AI Governance & Risk Assessment](docs/04-security-governance/NAWA_AI_Governance_and_Risk_Assessment.pdf)
- [Review Workflow](docs/03-document-ai-rag/NAWA_Review_Workflow.pdf)

### Cloud and production engineering

- [Cloud Operations](docs/06-cloud-devops/NAWA_Cloud_Operations.pdf)
- [DevOps, CI/CD & Deployment Guide](docs/06-cloud-devops/NAWA_DevOps_CICD_and_Deployment_Guide.pdf)
- [Monitoring & Observability Architecture](docs/06-cloud-devops/NAWA_Monitoring_and_Observability_Architecture.pdf)
- [Disaster Recovery & Business Continuity](docs/06-cloud-devops/NAWA_Disaster_Recovery_and_Business_Continuity_Plan.pdf)
- [Production Readiness Assessment](docs/06-cloud-devops/NAWA_Production_Readiness_Assessment.pdf)

### Case study

- [Bilingual Document Intelligence Case Study](docs/07-case-study/NAWA_Bilingual_Document_Intelligence_Case_Study.pdf)

## 11. Demonstration Workflow

The intended portfolio demonstration follows this sequence:

1. Upload synthetic Arabic and English supplier quotations.
2. Inspect extracted quotation fields.
3. Follow a field citation to the original document page.
4. Compare quotation totals and VAT.
5. Review a discrepancy.
6. Record a correction.
7. Inspect the updated comparison and review history.

A recorded walkthrough and reproducible setup instructions will be added after verification.

## 12. Engineering Evidence Roadmap

| Evidence | Current publication status |
|---|---|
| Architecture and technical documentation | Available |
| Business and software requirements | Available as drafts |
| Source-code implementation | Not yet linked |
| Reproducible automated test run | Not yet linked |
| Bilingual OCR and extraction benchmark | Pending |
| Retrieval and citation benchmark | Pending |
| Security verification report | Pending |
| CI/CD execution evidence | Not yet linked |
| Application screenshots and demo | Not yet linked |
| Production readiness approval | Not established |

This table describes evidence available through the public portfolio, not necessarily all work completed privately.

## 13. Engineering Principles

NAWA is developed around several enterprise engineering principles:

- **Traceability:** AI-generated or extracted values should reference source evidence.
- **Human accountability:** Uncertain or disputed outputs require review.
- **Deterministic validation:** Financial calculations should use explicit, testable rules.
- **Least privilege:** Users should only access authorized documents.
- **Reproducibility:** Evaluations should identify datasets, versions, and configurations.
- **Operational reliability:** Failures, retries, deployment changes, and recovery should be observable and testable.

## 14. Project Limitations

This repository currently emphasizes technical documentation.

Public source code, independently reproducible test results, benchmark datasets, and deployment evidence are not yet linked here.

Architecture specifications and production plans should be interpreted as engineering design documents unless accompanied by implementation and verification evidence.

---

**NAWA demonstrates the design and engineering approach for a bilingual enterprise document intelligence system, with ongoing work to strengthen reproducible implementation, evaluation, security, and operational evidence.**
