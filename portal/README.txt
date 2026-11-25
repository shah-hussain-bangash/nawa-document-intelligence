Nawa v0.6.4 - cross-language retrieval diagnostic

1. Keep Ollama running with embeddinggemma:300m installed.
2. Extract collect_hybrid_diagnostics.py beside nawa.py in the existing workspace.
3. In that folder run: py -3.12 collect_hybrid_diagnostics.py
4. Wait for Embedding inputs: 360/360. Upload the generated ZIP printed at the end.

The script automatically uses the existing project .venv and loads local .env.
It constructs a TEMPORARY SEEDED SYNTHETIC corpus and reads the shipped 100-question
fixture set. It does not connect to the active workspace DB, enumerate its uploads,
or include .env or credentials. It sends only synthetic input to the configured
local embedding endpoint. Raw, search-result and question-answering query formats
are captured together with raw/titled document embeddings.

The resulting ZIP contains vectors, fixture text, selected model metadata and
source hashes so ranking can be reproduced and evaluated without rerunning your
model for every proposed parameter change. It does not change application ranking
or .env settings. No dependency installation or application release update is needed.

The user-provided quality report showed 40/40 same-language targets found and
7/40 cross-language targets found. These are developer-authored, exact-title
fixtures, not an independently reviewed or production acceptance benchmark.

Seven tests passed, including a legacy-locale CLI run with a local MOCK provider,
synthetic-only export, invalid-vector/route refusal and archive preservation.
Real model vector capture remains a user-side step.
