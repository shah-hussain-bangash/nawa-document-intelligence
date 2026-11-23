# Phase 6 - Optional LLM RAG with citation validation

This demo builds on Phase 4 BM25 permission-filtered retrieval and Phase 5 extractive evidence. It adds a **mock provider** (offline, deterministic, no LLM) and an **opt-in OpenAI provider** that requests a generated answer. The same validation gate checks both providers.

## Quick start (from the repository root)

```bash
cd demo
python3 -m nawa_demo.rag_cli --tenant demo-a --principal reviewer-a --question 'Example English Supplies grand total 1050'
python3 -m nawa_demo.rag_cli --tenant demo-a --principal reviewer-a --question 'شركة المثال الضريبة ٤٥'
python3 -m nawa_demo.rag_cli --tenant demo-a --principal reviewer-a --question 'interplanetary antimatter quantum'
python3 -m unittest discover -s tests -v
```

The mock provider returns verbatim Phase 5 answer excerpts, not generated text. The CLI defaults to `--provider mock`, makes **no network request**, and does not require any API key. All new tests use this or scripted fake providers.

## Opt-in model experiment

Requires internet access, an OpenAI API account with usage enabled, and an `OPENAI_API_KEY` environment variable **set locally**. Calls may incur charges; never paste or commit an API key.

```bash
cd demo
read -s -p 'API key (input hidden): ' OPENAI_API_KEY; echo
export OPENAI_API_KEY
python3 -m nawa_demo.rag_cli --provider openai --tenant demo-a --principal reviewer-a --question 'Example English Supplies grand total 1050'
unset OPENAI_API_KEY
```

**Do not run the real provider in CI.** It is not automated or guaranteed to return an accepted answer; model capability, model availability, network, costs and output can vary. The experimental OpenAI path uses the Chat Completions JSON-object response format and Python standard library HTTP. The Responses API is generally recommended for new integrations; this adapter is intentionally minimal and should be migrated and verified before production use. It has not been validated against a live API in this package.

## Safety and interpretation

- Filter tenant/principal access **before** retrieval and model input. The CLI's identities are user-supplied simulations; this is **not authentication**. Do not deploy it as a multiuser service.
- Model receives only retrieved, authorized excerpts, not the full corpus. Document text is untrusted and is explicitly labeled as data in prompts.
- The response must be JSON with `answer` and `citations`, containing exact quotes tied to IDs returned by authorized retrieval. The server constructs citation metadata; it does not trust model-supplied file/page values.
- The complete answer must be a contiguous excerpt of one cited quote, and its content tokens must appear in cited quotes. This rejects paraphrases and stitched answers, including the tested swapped subtotal example. A literal extract can still omit a negation or necessary context; it is **not** semantic verification. Review the original source.
- `insufficient_evidence` means Phase 5 could not find sufficient lexical support. `rejected_ungrounded` means the proposed model answer did not pass the citation gate. Neither represents calibrated statistical confidence.
- The `mock` provider is not an LLM and does not demonstrate true generation. The opt-in OpenAI integration is unverified until a real end-to-end request succeeds.
- The examples are synthetic. No production ACLs, full prompt-injection defense, PII handling, audit logging, rate limiting, monitoring or security review. Never use real confidential supplier documents in a public repo or send them to a model without organizational authorization.
