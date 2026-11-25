# AI Workflow and Evaluation Specification

Retrieval, agents, evidence and measurable release quality

Version 1.0 | 6 November 2026 | Proposed development baseline

## 1. AI responsibility boundary

Models extract fields, summarise evidence and propose drafts. They do not decide permissions, compute authoritative totals, approve procurement or invent missing evidence. Deterministic code validates schemas, arithmetic and workflow transitions.
Start with an explicit workflow: intake → retrieve → extract → validate → draft → review pause → simulated outcome. Add routing/planning only when it improves a measured use case. Every run has a model, prompt, rule and dataset version record.

## 2. Retrieval and evidence

Preserve document version, page and table/span provenance during parsing. Apply tenant, document ACL, classification and effective-date filters before constructing model context. Benchmark lexical and multilingual embedding retrieval; add hybrid retrieval/reranking only when it improves held-out results.
Answers cite accessible versions and passages. When evidence is missing or conflicting, explain the limitation and request review or abstain. Do not treat model-reported confidence as calibrated probability. Permission checks apply again when opening a citation.

## 3. Extraction and tool contracts

Extraction returns typed fields with evidence references and unknown-value states. Validate dates, quantities, currencies and totals outside the model. Preserve reviewed corrections separately from model output.
Each tool declares name, input/output schemas, tenant/resource scope, allowed destinations, required permission, timeout, retry rule and idempotency strategy. MCP does not replace these controls. Tools receive only the data needed for the permitted operation.

## 4. Evaluation dataset

Begin with at least 100 reviewed questions, balanced between Arabic and English, linked to a versioned document corpus. Include answerable, unanswerable, conflicting-policy, table, scan, permission-denied and mixed-language cases. Add separate workflow, extraction and adversarial datasets.
Split by document family/case; keep a held-out set. Record expected answer facts, acceptable citations, relevant documents, expected tool/action and review requirement. Use a second reviewer for ambiguous ground truth and document disagreement resolution.

## 5. Metrics and proposed targets

Retrieval: recall@5 against labelled relevant evidence. Citation precision: supported, correct citations divided by emitted citations. Extraction: precision/recall/F1 by field, language and document type. Answers: correctness, groundedness and abstention quality using a defined rubric.
Candidate pilot targets are recall@5 ≥85%, citation precision ≥95% and key-field extraction F1 ≥90%. These are proposed thresholds, not measured results. Confirm feasibility after the baseline and report sample counts and uncertainty. Never change held-out labels just to pass a target.

## 6. Workflow and operational measures

Measure case completion by scenario, reviewer correction rate, tool schema validity, stale approval rejection, duplicate-outcome prevention, recovery success and safe cancellation. Security/authorisation tests must all pass independently of answer quality.
Record latency percentiles, tokens, provider charges, OCR/embedding expense and cost per successful case. Separate ingestion from interactive latency. Report hardware, model version, concurrent load and failure rates; do not present an unloaded demo as a production benchmark.

## 7. Agent runtime guardrails

Bound graph steps, model calls, tokens, elapsed time and per-tenant spending. Use bounded retries for transient errors and schema repair. Persist checkpoints with tenant scope. Revalidate membership, evidence revision and approval before resume.
Do not expose raw internal reasoning as an audit artifact. Record observable inputs/outputs, evidence, tool proposals, policy decisions and outcomes, with redaction. Fail visibly when an approved provider is unavailable; only use policy-compatible fallbacks.

## 8. Adversarial and regression testing

Test document instructions that request secrets/tools, fabricated citations, poisoned policy text, forbidden URLs, invalid tool arguments, cross-tenant queries, revoked access, prompt-based approval bypass and repeated side-effect requests. Enforce invariants in code rather than trusting model obedience.
CI runs deterministic contract/workflow/security tests. A controlled, versioned evaluation run checks model-dependent behaviour on relevant changes. Use human review for sampled failures; an LLM judge alone is not ground truth. Keep live-provider evaluation separate from mocked tests.

## 9. Release evidence

Publish dataset/version, split method, model/prompt/rule identifiers, parameters, language-level metrics, failure examples, cost and known limitations. Require passing mandatory isolation, approval-integrity and tool-authorisation scenarios; critical failures block release.
Future forecasting is a separate model: use time-based splits, compare with an appropriate naive baseline and report error/uncertainty. Add it only after the procurement evidence and approval workflow is reliable.
