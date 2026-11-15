# Phase 5: Grounded, extractive Q&A with source citations

This phase extends the Phase 4 **synthetic permission-filtered BM25** demonstration. Answers are **verbatim sentences from the authorized retrieved passage** with document ID, version, page, source file, evidence method and exact supporting quote. No generative LLM or neural RAG is used.

## Run (repository root)

```bash
cd demo
python3 -m nawa_demo.qa_cli --tenant demo-a --principal reviewer-a --question 'Example English Supplies grand total 1050'
python3 -m nawa_demo.qa_cli --tenant demo-a --principal reviewer-a --question 'شركة المثال الضريبة ٤٥'
python3 -m nawa_demo.qa_cli --tenant demo-a --principal reviewer-a --question 'interplanetary antimatter quantum'
python3 -m unittest discover -s tests -v
```

## Guarantees and boundaries

- Returned `answer` equals the cited sentence (`quote`) and occurs verbatim within an authorized source passage. No model-generated financial facts.
- Unknown or weakly supported questions return `status: insufficient_evidence`, `answer: null`, and zero citations. The lexical gate is a **heuristic**, not a calibrated correctness or entailment score.
- The same trusted caller permissions as Phase 4 are used to filter passages **before ranking**. CLI `--principal` and `--tenant` are self-asserted demo values, **not authentication or production security**.
- Arabic and English rely on lexical token matching; not cross-language semantic Q&A. A returned evidence sentence does not guarantee it *logically answers* a natural-language question.
- Fixture `source` names are **synthetic metadata**, not proof that an underlying PDF was processed. OCR content may contain errors.
- This intentionally does not use an LLM, vector database, embeddings, tool calls, real documents, live identity, prompt-injection controls, or production evaluation.
- Test with synthetic data only. Do not upload private supplier documents into this public repository.
