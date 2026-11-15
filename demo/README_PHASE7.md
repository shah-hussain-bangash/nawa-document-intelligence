# Phase 7 — Reproducible RAG evaluation and security regression tests

Phase 7 **adds evaluation and scripted adversarial tests**, without silently changing the Phase 6 retrieval, citation gate, or mock/opt-in model providers. No API key, external model or internet is needed.

## Run (from `demo/`)

```bash
python3 -m nawa_demo.eval_cli
python3 -m nawa_demo.eval_cli --output phase7_report.json
python3 -m unittest discover -s tests -v
```

The CLI exits with code `1` if any evaluation expectation fails, `2` for invalid inputs, and `0` on a fully passing synthetic suite. Reports record case IDs, expected/observed status, authorized citation IDs, and explicit limitations—not answer bodies or source text.

The 11 deterministic cases cover English, Arabic and policy evidence, unknown/restricted/cross-tenant refusal, authorized admin access, and scripted response attacks (invented number, nonexistent citation, modified quote, and a prompt-injection-style instruction output).

**Metrics:** `status_accuracy` is the fraction of exact expected-status/citation/abstention checks satisfied. It is NOT ground-truth answer correctness, semantic faithfulness, precision/recall over a representative dataset, or an LLM security benchmark. `all_passed` means these 11 fixture checks pass, not that the system is safe against arbitrary adversaries.

## Security limitations and outstanding work

- The Phase 6 lexical gate checks **tokens and exact citation quotes**, not logical entailment. A sentence can rearrange supported words to assert a **false relationship** and still pass. Phase 7 does not claim to solve this.
- Tests simulate attacks by returning scripted outputs. They do not show that actual LLMs follow prompt-injection defenses when consuming malicious documents.
- Corpus tenant IDs and principal IDs are self-asserted demo values. Production authentication, authorization, document revocation, deletion propagation, audit trails and rate limiting remain unimplemented.
- The `source` field of synthetic fixtures is evidence metadata, not an independently validated reference to a PDF file.
- Test cases are small and synthetic; no Arabic OCR accuracy, real-model output quality, live API behavior, or adversarial red-team coverage has been measured.
- Do not commit `phase7_report.json` unless intended; it is generated. Do not use real confidential supplier data in public tests.

Future work should add trustworthy backend identity, explicit prompt-injection segmentation, real labeled bilingual evaluation corpora, semantic claim verification, and controlled model evaluations with budgets and privacy review.
