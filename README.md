# NAWA | Bilingual Document Intelligence

NAWA is an enterprise document intelligence project for comparing Arabic and English supplier quotations. It uses OCR and page-linked evidence to help reviewers trace extracted values, verify VAT comparisons, and resolve discrepancies. I built the interface, APIs, data layer, processing workflows, and tests as sole developer. Portfolio demonstrations use synthetic data.

**Start here:** [Case study](docs/NAWA_Bilingual_Document_Intelligence_Case_Study.pdf) · [System architecture](docs/NAWA_System_Architecture.pdf) · [AWS development workspace sign-in](https://zenith-ai-workspace.duckdns.org/sign-in)

## Technical portfolio

| Area | Evidence |
| --- | --- |
| Enterprise Solutions Architecture | [System Architecture](docs/NAWA_System_Architecture.pdf) and [Architecture Decisions](docs/NAWA_Architecture_Decisions.pdf) |
| Generative AI Engineering | [Document AI & RAG](docs/NAWA_Document_AI_and_RAG.pdf), [Evaluation Plan](docs/NAWA_Arabic_and_English_Evaluation_Plan.pdf), and [Evaluation Report](docs/NAWA_Evaluation_Report.pdf) |
| Agentic AI Engineering | [Review Workflow](docs/NAWA_Review_Workflow.pdf), covering bounded automation, exception handling, and human decisions |
| Cloud & AI Infrastructure | [Cloud Operations](docs/NAWA_Cloud_Operations.pdf), covering the AWS development topology and proposed recovery procedures |
| AI Security & Governance | [Security Design](docs/NAWA_Security_Design.pdf), covering trust boundaries, roles, lifecycle controls, and verification |

## Walkthrough

1. Upload synthetic Arabic and English quotations.
2. Open an extracted value and follow the citation to its original page.
3. Inspect a VAT discrepancy, record a reviewer correction, and refresh the comparison.

## Evidence status

The résumé reports 123 passing local automated tests, local backup and restore validation, and Cognito sign-in for NAWA in the AWS development workspace. The evaluation report is a pre-run edition. Bilingual benchmark measurements, control-level verification results, and cloud recovery observations are pending. The architecture and security PDFs identify proposed controls.
