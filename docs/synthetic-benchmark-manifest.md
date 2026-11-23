# Synthetic bilingual benchmark metadata check

The existing evaluation plan proposes 60 synthetic or permissioned quotations, balanced across Arabic, English and mixed language, with 30 development and 30 holdout documents and at least 60 holdout queries. Those counts are **proposed**, not observed results or approved release thresholds. This prototype accepts synthetic metadata only; it does not create the dataset.

`nawa_demo.synthetic_benchmark_manifest.inspect_manifest` checks declared document and query identifiers, source type, language, format, split and label status. It rejects duplicate IDs, a declared layout template shared across development and holdout, inconsistent answerability, and expected documents outside the query's split. It returns counts so missing coverage is visible. The manifest contains synthetic IDs and labels only; do not put document text or personal information in it.

The checker cannot detect undeclared near-duplicate layouts, validate the cited source, establish that a principal is authorized, or determine whether labels marked `reviewed` were independently reviewed. A successful metadata check is not a benchmark score, a privacy or access-control test, or a release approval. Human bilingual review and adjudication, a frozen holdout, source provenance, real evaluation runs and observed metrics remain open.
