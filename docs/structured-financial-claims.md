# Synthetic structured financial field check

This offline experiment addresses the case-study example in which a lexical checker accepted “Subtotal AED 1050.00” although the cited passage assigned AED 1000.00 to subtotal and AED 1050.00 to the grand total. It is not connected to the dashboard, generated answers, approvals or retrieval.

`check_structured_claim` compares a typed field and decimal amount with one complete, narrowly formatted synthetic source line. The currently recognized fields are subtotal, VAT amount and grand total, with selected English and Arabic labels and an explicit AED currency. Arabic-Indic and Persian digits are normalized. A match is still marked `requires_human_review`.

The single-line restriction means the original multi-field passage, grouped numbers, missing currencies, prose and unsupported layouts do not produce a match. This is deliberate abstention, not evidence that the source is wrong. A caller must separately verify the original document, exact source line, source integrity, version and authorization. The routine does not validate a free-text generated answer, determine the meaning of a whole document, perform financial arithmetic or make a human decision. A malicious or fabricated source line can still produce a match.

The tests are small, hand-authored synthetic cases and do not establish model accuracy, production security or bilingual performance. Before any integration, independently reviewed evaluation data and a documented policy for conflicting sources, currency, rounding, formatting and unsupported cases are needed.

The separate `validate_generated` path now additionally requires the entire answer to be a contiguous excerpt from one cited quote. The documented swapped-subtotal example is rejected in a regression test. This is an extractive restriction, not a connection to `check_structured_claim`, and it can reject useful paraphrases. A verbatim fragment can omit context or negation; source verification and human review remain necessary.
