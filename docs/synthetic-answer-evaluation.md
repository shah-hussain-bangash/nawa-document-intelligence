# Synthetic answer-level evaluation

Run from the `demo` directory:

```powershell
python -m nawa_demo.synthetic_answer_evaluation --cases samples/retrieval/synthetic_answer_cases.json
```

This 12-case hand-authored fixture exercises the offline extractive function only. It has four cases labeled answerable and eight labeled for abstention, with English and Arabic present dates, paraphrases, explicit absence, unknown or pending values, a conflicting date and instruction-like source text. Labels are illustrative and were not independently reviewed. No real model or portal flow is exercised.

One local run reported six false answers among the eight abstention-labeled cases, two false abstentions among the four answerable cases, and no wrong expected excerpts among the answered positive cases. In particular, the current fixed-phrase rule catches the included "not specified" examples but labels unknown, pending, conflicting and instruction-like examples as answered. The instruction-like case tests output labeling only; it does not show that an instruction was executed. Paraphrases without matching tokens were withheld despite the fixture label.

These results are not an estimate of production accuracy or a safety certification. They show why lexical coverage and a short phrase list cannot establish semantic support. Keep generated answers and source text subject to human review. An independently reviewed bilingual dataset, a documented adjudication process, relevant adversarial cases and evaluation of the actual deployed pipeline remain open.
