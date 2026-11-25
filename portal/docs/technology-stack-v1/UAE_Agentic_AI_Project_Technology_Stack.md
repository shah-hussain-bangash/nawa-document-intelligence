# UAE Sovereign Agentic AI — Technology Stack

Version 1.0 | 6 November 2026 | Proposed stack; implementation pending.

## 01 / Stack summary and selection rules

UAE Sovereign Agentic AI — project-specific technology reference. Version 1.0. Proposed stack; application implementation is pending.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| Core engineering | Python 3.12+; TypeScript; SQL; Git | Foundation |
| Backend and data | FastAPI; Pydantic v2; Uvicorn; SQLAlchemy; Alembic; PostgreSQL + pgvector | Core |
| User experience | React + Vite; bilingual localisation; evidence and approval console | Core |
| Documents and AI | Versioned storage; one parser/OCR pipeline; one approved model/embedding route; LangGraph | Staged core |
| Security and quality | OIDC; RBAC/ABAC; pytest; browser tests; reviewed evaluation datasets | Core |
| Delivery and operation | Docker Compose; GitHub Actions; approved cloud/IaC; redacted telemetry; restore tests | Staged core |

### How to read this document
Core means required for the selected design. Staged core means required when that capability is implemented. Choose one means alternatives, not simultaneous installations. Optional means adopt only for a measured requirement.


### What is actually installed or implemented?
This is a recommended architecture stack, not an inventory of verified dependencies. The repository currently contains project documentation. Exact versions and lockfiles must be selected and tested during implementation.


### First development increment
Start with Python, FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, React/TypeScript/Vite, Docker Compose, Git and pytest. Add identity before shared exposure; add AI, workers and extensions in phase order.

## 02 / Backend, persistence and asynchronous work

Build a modular backend with explicit contracts. Logical modules do not require separate microservices.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| Python 3.12+ | API, workers, agent workflows and predictive ML | Core |
| FastAPI + Uvicorn | Typed HTTP API and ASGI serving | Core |
| Pydantic v2 | Settings, API schemas and validated extraction/tool output | Core |
| SQLAlchemy + Alembic | Data access, transactions and versioned schema migrations | Core |
| PostgreSQL | Cases, revisions, memberships, ACLs, approvals, audit and runs | Core |
| pgvector | Embedding storage and vector similarity inside PostgreSQL | Staged core |
| HTTPX | Service HTTP clients and API integration testing | Core |
| Redis + Celery | Ingestion jobs and bounded background work; managed queue is an alternative | Choose one queue design |
| Python Decimal | Reproducible prices, taxes, quantities and rounding | Core practice |

### Data integrity
Use tenant-scoped references, optimistic concurrency and atomic case/approval updates. Keep model calls outside long database transactions. Database/job records, not a transient cache alone, preserve business state.


### When to introduce jobs
Add asynchronous execution when OCR, parsing and indexing exceed interactive request limits. Design idempotency and reconciliation; queue retries alone do not guarantee exactly-once side effects.

## 03 / Document intelligence, storage and retrieval

Preserve source versions and page/table provenance. Authorisation must cover every derived artifact, including embeddings.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| S3-compatible object storage | Private originals, parsed artifacts and reports; AWS S3 is one cloud option | Staged core |
| Local storage / MinIO | Development alternatives; review licence and operating requirements | Choose supported local option |
| Docling / PyMuPDF | PDF text, layout and table parsing; choose a licensed parser baseline | Choose one baseline |
| Tesseract OCR + language data | OCR for English/Arabic scans when needed | Conditional |
| Document metadata + hashing | Immutable versions, effective dates, source register and access policy | Core application capability |
| PostgreSQL lexical search | Keyword retrieval baseline; benchmark Arabic tokenisation | Core baseline |
| pgvector + multilingual embeddings | Semantic search with tenant/ACL/version filters | Staged core |
| Sentence Transformers / provider embeddings | Local or approved hosted embedding implementation | Choose permitted route |
| Reranker | Improve ranked evidence only when benchmarks justify cost | Optional |

### Retrieval design
Benchmark lexical and vector baselines, then combine them if useful. Keep original Arabic text distinct from search normalisation. Retrieval scores are not calibrated answer-confidence probabilities.


### Lifecycle and licensing
Review parser/model licences for the actual distribution and hosting model. Revoke/delete originals, text, chunks, vectors and caches consistently. Governance is not solved by a storage product alone.

## 04 / Models, agents and controlled integrations

Models propose and extract. Deterministic services calculate, authorise, approve and control state transitions.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| Approved provider SDK | Chat/extraction and embeddings using validated structured output | Choose approved provider |
| OpenAI API / Azure OpenAI / Bedrock | Hosted route candidates; verify exact service, model, terms and location | Alternatives, not all required |
| Ollama / vLLM | Local experiments or private model serving; suitability differs by workload | Optional private route |
| LangGraph | Bounded stateful workflow, checkpoints and human-review pause/resume | Staged core |
| LangChain | Convenience integrations when they reduce useful work | Optional |
| MCP | Standard connector interface for a defined approved integration | Optional interface |
| Pydantic + explicit tool registry | Typed tool inputs/outputs, schema validation and allowlisted operations | Core |
| Application model gateway | Classification routing, budgets, timeouts, allowed destinations and fallbacks | Core capability |
| LiteLLM / another gateway product | Provider abstraction when multiple approved routes justify it | Optional |

### Model choice remains open
Select exact models against Arabic/English quality, structured extraction, latency, cost, licence and processing policy. This document makes no claim about current model availability or UAE-region support.


### Agent controls
Bound steps, tokens, elapsed time and retries. Revalidate scope and evidence on resume. MCP and an agent framework are not authorisation mechanisms. Real payments, awards and supplier messages remain outside the sandbox.

## 05 / Frontend, bilingual experience and identity

The interface must make evidence, uncertainty, processing status and human authority visible.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| React + TypeScript + Vite | Case workspace, citation viewer, comparison and review queue | Core |
| i18next / equivalent | English/Arabic translations and language switching | Choose one localisation library |
| RTL CSS + semantic HTML | Reading order, keyboard operation, labels and mixed-direction content | Core practice |
| Tailwind CSS + shadcn/ui | Styling and accessible component baseline | Recommended option |
| TanStack Query | Server-state fetching, caching and invalidation | Recommended option |
| React Hook Form + Zod | Forms and client validation; server remains authoritative | Optional |
| Keycloak / approved OIDC provider | Login, SSO, signing keys and identity federation | Choose one |
| OIDC / OAuth 2.0 + applicable PKCE/session controls | Verified identity and secure browser-session flow | Core standards |
| RBAC / ABAC in application services | Roles plus tenant/resource/classification access rules | Core capability |

### Identity boundaries
Verify issuer, audience, signature, expiry and membership. Choose secure session/token handling deliberately, including CSRF/CORS controls as applicable. Never treat a browser tenant ID as proof of membership.


### Approval experience
Show case revision, evidence versions, assumptions and reviewer reason. New evidence invalidates old approval. Client-side validation or hidden controls cannot replace backend permissions.

## 06 / Predictive ML, AI evaluation and testing

Use separate evidence for deterministic tests, live model behaviour and predictive forecasting.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| pytest + HTTPX | Unit, database/API integration, authorisation and workflow tests | Core |
| Playwright | Arabic/English browser journeys, review and failure states | Staged core |
| RAGAS OR DeepEval | Supporting RAG/answer evaluation with a reviewed rubric | Choose one if useful |
| Reviewed datasets + human annotation | Expected fields, relevant evidence, citations and abstention | Core requirement |
| Langfuse | Prompt/run trace metadata, datasets and usage; govern hosting/redaction | Recommended AI tool |
| Pandas OR Polars | Forecast data preparation and feature work | Choose one baseline |
| scikit-learn + XGBoost | Baselines and candidate workload/demand models | Forecasting phase |
| MLflow / versioned equivalent | Experiment, model and artifact tracking | Forecasting phase |
| SHAP / Evidently | Explanations and drift tooling when the model/use case warrants it | Optional |

### Evaluation rules
Separate held-out examples by case/document family. Report Arabic/English and field-level results. Measure citation precision, recall@k, answer correctness, extraction F1, workflow completion, cost and latency. An LLM judge alone is not ground truth.


### Forecasting rules
Use chronological splits, compare a naive/seasonal baseline, prevent future-data leakage and report errors/uncertainty. Predictions are advisory. PyTorch and fine-tuning are unnecessary until an actual model requirement justifies them.

## 07 / Containers, cloud and infrastructure delivery

Local development comes first; cloud services are introduced only with an authorised deployment scope.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| Docker + Docker Compose | Repeatable local API, database, worker, storage and identity services | Core |
| GitHub Actions | Locked build/test, scans and controlled artifact promotion | Core |
| Terraform / approved IaC equivalent | Versioned network, compute, IAM, storage and backup provisioning | Deployment phase |
| EC2 OR managed containers such as ECS | Runtime candidates based on measured capacity/operating needs | Choose one |
| RDS PostgreSQL OR secured PostgreSQL | Managed database candidate or approved operated deployment | Choose one |
| S3 / approved private object storage | Versioned private evidence and artifacts | Choose one |
| IAM + VPC + TLS ingress | Least privilege, private services and controlled network entry | Core cloud controls |
| Secrets Manager + KMS / approved equivalents | Secret injection/rotation and encryption key control | Core cloud controls |
| SQS / managed queue | Alternative to the selected Redis/Celery queue design | Optional replacement |

### Sovereignty review
Verify inference, embeddings, OCR, telemetry, backups, recovery and support/subprocessor access separately. Service location and terms must satisfy the selected profile. A UAE application region does not establish complete data residency.


### Deployment gate
Deploy the same tested immutable artifact to staging, exercise safe migrations and the full synthetic case, then demonstrate rollback and backup restore. Do not claim production readiness from a container build alone.

## 08 / Security, observability and recovery

Use a small coherent operations stack. Several overlapping logging or monitoring products are not automatically better.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| OpenTelemetry | Correlated vendor-neutral traces/metrics across API, jobs and workflows | Recommended baseline |
| Prometheus + Grafana OR cloud monitoring | Metrics, dashboards, workload objectives and alerts | Choose coherent baseline |
| CloudWatch | AWS service logs/metrics when AWS is the selected deployment | Cloud option |
| Trivy OR equivalent scanner | Container/dependency findings and SBOM support | Choose one |
| Business audit + integrity controls | Actor, tenant, evidence revision, decision and protected history | Core application capability |
| OPA | Central policy-as-code when complexity justifies another service | Optional |
| Presidio / reviewed redaction pipeline | Supporting sensitive-data detection; not a complete privacy guarantee | Optional |
| Encrypted backups + restore tooling | Database/object recovery; reapply revocations and deletions | Core operational capability |
| Rate / file / token / spending limits | Bound resource use and abuse at relevant boundaries | Core controls |

### Telemetry restrictions
Redact sensitive prompts and document contents by default. Protect trace destinations with the same classification/location policy as other derived data. Keep business audit separate from debug logging.


### Recovery proof
Set RTO/RPO from operating needs, measure actual recovery, reconcile queued work and preserve approval integrity. Append-only APIs are not tamper-proof storage; restrict writers and add separately protected evidence where required.

## 09 / Developer tools, documentation and adoption order

Choose tools that support understanding, reproducibility and measured results rather than collecting products.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| Git + GitHub | Source history, review, issues and release records | Core |
| VS Code OR Cursor | Primary editor/debugger; using both is not required | Choose preferred editor |
| Ruff + mypy / selected type checker | Python formatting/lint and useful type checks | Recommended |
| pre-commit | Fast local quality hooks aligned with CI | Recommended |
| Postman OR Bruno | Manual API exploration using synthetic data | Optional |
| DBeaver OR pgAdmin | Database inspection with least-privilege access | Optional |
| Markdown + Mermaid / Graphviz | Living specifications, ADRs, diagrams and runbooks | Recommended |
| MkDocs | Documentation website when the pack outgrows repository pages | Optional |

### Phase mapping: foundations through evidence
Phases 00–02: requirements, architecture, data policy and threat model. 03–04: Git, pinned runtimes, FastAPI/PostgreSQL, React, Docker and CI. 05–06: OIDC, permissions and audit. 07–09: datasets, storage, parsing and OCR.


### Phase mapping: AI through operation
10–12: model gateway, embeddings, retrieval and cited answers. 13–16: procurement, approvals, LangGraph and complete bilingual console. 17–18: HR/service desk and forecasting. 19–20: evaluations, security and workload testing. 21–25: IaC/cloud, staging, pilot, recovery and operation.

## 10 / Decisions, deferred tools and official references

Resolve alternatives in architecture decision records before installing or provisioning them.

| Technology / choice | Purpose | Adoption |
|---|---|---|
| Choose before implementation | Exact supported versions; package manager; model/embedding route; identity provider; parser licence | Record rationale |
| Choose before cloud deployment | Approved region/profile; compute/queue/storage design; budget; retention; support access | Verify service-specific terms |
| Defer until measured need | Kubernetes/EKS, Helm, Istio, Kafka, Spark, Flink, several vector databases | Do not install initially |
| Defer model complexity | Multiple agent frameworks, neural forecasting, fine-tuning, distributed serving | Require a benchmarked use case |
| Document readiness honestly | Installed tooling ≠ working integration ≠ evaluated release ≠ authorised real-data operation | Separate evidence |

### Official starting points: application and AI
FastAPI: https://fastapi.tiangolo.com/ ; PostgreSQL: https://www.postgresql.org/docs/ ; pgvector: https://github.com/pgvector/pgvector ; React: https://react.dev/ ; LangGraph: https://docs.langchain.com/oss/python/langgraph/overview ; MCP: https://modelcontextprotocol.io/ .


### Official starting points: delivery and operations
Docker: https://docs.docker.com/ ; AWS: https://docs.aws.amazon.com/ ; Terraform: https://developer.hashicorp.com/terraform/docs ; Keycloak: https://www.keycloak.org/documentation ; OpenTelemetry: https://opentelemetry.io/docs/ ; MLflow: https://mlflow.org/docs/latest/ .


### Version and source note
Based on the supplied roadmap/technology PDFs, architecture and 26-phase implementation guide. These links are starting points, not live verification of pricing, current versions, model availability or regional support. Validate selected versions, licences and service terms before implementation. No subscription, licence or cloud purchase was made.
