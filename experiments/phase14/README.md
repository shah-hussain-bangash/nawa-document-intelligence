# Phase 14: initial synthetic BM25 baseline

See [ACCEPTANCE.md](ACCEPTANCE.md) for the roadmap checkpoint, open security
finding and remaining Phase 14 acceptance work.

This is an isolated, offline measurement of the existing Phase 4 lexical
retrieval code and its three original synthetic labeled questions, copied from
the Phase 13 draft. It does not change either running NAWA application.
The standard-library unit checks do not call Ollama. The model probes are
explicitly invoked, send only these synthetic fixtures to a local Ollama
service and are not part of automated CI. The GitHub draft depends on the
unmerged Phase 13 draft and does not deploy or integrate these experiments.

Run in this directory:

```powershell
python -m unittest -v test_benchmark
python benchmark.py
python expanded_benchmark.py
python -m unittest -v test_benchmark test_compare_retrieval
python compare_retrieval.py
python unknown_probe.py
python version_probe.py
python -m unittest -v test_lifecycle_fixture
python -m unittest -v test_benchmark test_compare_retrieval test_lifecycle_fixture test_fixture_integrity
python lifecycle_probe.py
python -m unittest -v test_support_probe
python support_probe.py
python -m unittest -v test_semantic_probe
python semantic_probe.py
python -m unittest -v test_injection_probe
python injection_probe.py
python -m unittest -v test_review_only
python -m unittest -v test_hybrid_review
python hybrid_review_probe.py
python -m unittest -v test_phase13_snapshot_fixture
python -m unittest -v test_resolve_review_evidence
```

The 17 November 2026 local run gave Recall@5, MRR@5, and binary nDCG@5
of 1.0 each on three queries. Two ranking-metric unit tests passed. One
unknown-query and two fixture access-boundary smoke checks returned no
passages. The measured latency is a single local run of the search call,
excluding index construction and network or embedding costs; it is not a
performance benchmark.

The corpus is tiny and the questions mostly overlap the document wording.
These scores do not establish real-world retrieval quality, multilingual
paraphrase performance, semantic support, production security, or any benefit
from embeddings. The fixture identity and ACLs are supplied in code; the
baseline is not connected to the Phase 12 identity service, live document
lifecycle, or database. A smoke test is not evidence of a complete ACL review.

The additional hand-authored set has 12 passages and 10 labeled queries. A
local run gave Recall@5 0.90, MRR@5 0.85 and binary nDCG@5 0.863. One Arabic
warranty paraphrase returned no results; an English payment paraphrase ranked
the expected passage second. The direct matches performed better in this
small constructed set. Both versions of a synthetic quotation appeared in
version-specific searches, which demonstrates why lifecycle/version filtering
needs separate implementation and tests. Access and unknown-query checks are
small fixture smoke tests, not a security assessment.

An untrusted instruction-like passage was also returned for an unrelated
query. The benchmark never sends it to a language model and therefore does not
test prompt-injection resistance. The labels and cases were authored together;
they are not an independent or held-out evaluation set.

Next, expand and independently review the labels, add held-out paraphrases and
explicit deletion/revocation scenarios. Compare the same set across lexical,
vector and hybrid methods, with repeatable latency and semantic-support
evaluation.

## Local model comparison

On 17 November 2026, a single local synthetic run compared BM25, Ollama
`embeddinggemma:300m` cosine similarity, and equal reciprocal-rank fusion
(RRF constant 60). The same 10 hand-authored queries and 12 passages were
used; two inaccessible fixture passages were filtered before embedding.
Results are in `comparison-result.json`.

| Method | Recall@5 | MRR@5 | nDCG@5 |
| --- | ---: | ---: | ---: |
| BM25 | 0.90 | 0.85 | 0.863 |
| Vector | 1.00 | 1.00 | 1.00 |
| Hybrid | 1.00 | 1.00 | 1.00 |

Vector and hybrid retrieved the expected Arabic warranty paraphrase missed
by BM25, and ranked the English payment passage first. These are preliminary
results on a tiny, non-independent dataset; they do not prove a general
improvement or production readiness. Vector and hybrid ranking always return
candidates in this prototype: no relevance threshold or unknown-answer
abstention has been calibrated. Both quotation versions may be returned.

One local run averaged roughly 0.04 ms per BM25 query and 1.4 seconds per
vector or hybrid query, with about 13 seconds to embed authorized documents.
These timings are a single uncalibrated run and include local model request
overhead; they are not a performance guarantee. The four unit tests cover
metric examples, cosine/fusion and fixture filtering before embedding. They do
not establish authenticated access control, deletion propagation, semantic
entailment, or resistance to prompt injection. No real data was used.

## Unknown questions and conflicting versions

The score probe includes 26 hand-authored unanswerable questions (three
unrelated and 23 about absent information) alongside the 10 answerable cases.
Every question received a ranked passage, including all 26 unanswerable
ones. In this local run the top similarity scores ranged from 0.611 to 0.861
for answerable cases and 0.203 to 0.844 for unanswerable cases. Eleven of
the unanswerable questions scored at least as high as the lowest-scoring
answerable question. For example, an absent approval identity scored 0.844
against a related policy passage. A threshold low enough to retain all 10
answerable cases would also retain those 11 unsupported cases. These labels
are hand-authored and not independently reviewed. The result does not
establish an operational threshold or measure semantic entailment.
It requires a larger, independently labeled calibration set and held-out
evaluation. A high similarity score does not prove an answer is supported.
`unknown-probe-result.json` stores the synthetic results.

The separate version probe explicitly assumes Cedar v1 is original and v2
is latest. For the latest-version question, vector ranking put v1 first,
while hybrid put v2 first. For the original-version question, all three
methods ranked v2 first. No lifecycle or version policy is applied. These
examples demonstrate that ranking alone cannot select the correct version;
the future service must apply trusted version and access rules before
retrieval and again before context assembly. Results are in
`version-probe-result.json`.

## Synthetic lifecycle-filter experiment

`lifecycle_fixture.py` exercises a caller-supplied in-memory snapshot:
current passages are eligible; superseded passages are excluded unless the
trusted caller explicitly permits history for a document; deleted and revoked
passages are excluded. It filters tenant and principal fixtures before sending
passages for embedding, and rechecks result candidates against a fresh
snapshot before returning them. Missing metadata fails closed. The caller
must authorize any history selection; the function does not provide that
authorization itself.

In `lifecycle_probe.py`, the synthetic snapshot marks Cedar v1 superseded.
The local embedding model then ranks v2 first for the latest-version question
and v1 is not indexed for that query. Seven focused tests pass, including
fixture deletion, revocation, membership change and missing metadata. This is
an isolated experiment: it is not connected to Phase 12 identities, Phase 13
version records, a real deletion process, or LLM context assembly. The
separate initial and recheck steps do not establish atomic access enforcement
or remove the possibility of a change after the recheck. Independent review
and integration tests remain necessary.

## Evidence-support heuristic experiment

An additional 20 hand-authored bilingual claim/passage pairs contain 10
supported and 10 unsupported examples, including changed numbers, reversed
timing and added details. They are deliberately small and have not been
independently reviewed. `support_probe.py` evaluates string heuristics; it
does not implement semantic entailment or generate answers.

| Heuristic | Supported accepted | Supported missed | Unsupported accepted | Unsupported rejected |
| --- | ---: | ---: | ---: | ---: |
| Normalized exact substring | 7 | 3 | 0 | 10 |
| At least 80% token overlap | 7 | 3 | 8 | 2 |

On this set, the overlap heuristic accepted claims with changed delivery
periods, changed warranty terms and payment before rather than after invoice
receipt. Exact substring avoids those examples but misses supported
paraphrases and, by itself, does not verify that an independently generated
claim is entailed by a cited excerpt. Neither heuristic is suitable as a
production semantic-support gate. The full fixture results are saved in
`support-probe-result.json`; ten focused tests passed on the local run.

Next, use independently reviewed, larger bilingual claim/evidence labels,
including contradictions and unsupported additions, to assess candidate
semantic validators and safe abstention. Measure false acceptance separately;
preserve human review and avoid treating model confidence as proof.

## Local semantic-validator experiment

`semantic_probe.py` sends only synthetic claims and their corresponding
passages to the local Ollama `qwen3:8b` model. Ground-truth labels and
descriptive case IDs are withheld. A single structured-output request assesses
the same 20 hand-authored examples; invalid, missing, duplicated or truncated
model results are rejected by the harness.

In one local run the model agreed with all 20 fixture labels: 10 supported
accepted, 10 unsupported rejected, no false acceptances and no supported
examples missed. The run took approximately 12 seconds. Twelve focused unit
tests passed, including checks that labels are withheld and malformed output
is rejected. These results are preliminary: the set is tiny, hand-authored,
not independently reviewed, and evaluated in a single batch. The model may
make errors or follow malicious source text; adversarial injection and safe
abstention have not been established. Results do not validate production
use, and a model verdict is not proof of entailment.

## Adversarial evidence experiment

Eight paired English/Arabic synthetic claim examples compare clean evidence
with evidence containing instructions that attempt to change the evaluator's
verdict. These are manually authored fixtures, not an independent security
assessment. In one local run, `qwen3:8b` classified all eight clean
controls correctly. With the instruction-like text included, it classified
all eight incorrectly: six unsupported claims were accepted, and two
supported claims were rejected. Both a single combined prompt and a separate
system-message/user-message formulation produced the same result.

This is a demonstrated failure for this model, prompt and batch of fixtures,
not a measurement of all possible attacks or defenses. The experimental model
checker must not be used as an automatic evidence-approval gate. Results are
saved in `injection-probe-result.json`. Thirteen local unit tests passed;
they validate the harness, not resistance to malicious documents.

## Review-only decision boundary

`review_only.py` is a separate fixture prototype that routes either model
verdict to `requires_human_review`; a verdict never creates an approval.
It rechecks synthetic candidate IDs against the supplied identity and
lifecycle snapshot, returning `unavailable` for invalid, revoked, stale or
unauthorized candidates. It returns citation metadata and the model's
suggestion, not a verified claim. The local focused suite now has 15 passing
tests, including invalid suggestions and revoked candidates.

This is not connected to NAWA, an actual reviewer interface, a trusted identity
service, or database transactions. The caller remains responsible for fresh
trusted data and safe rendering. It does not sanitize malicious content,
prevent human reviewer manipulation, eliminate post-check race conditions,
or make the model injection-resistant. Independent security review and a
real human decision workflow remain required.

## Combined synthetic retrieval experiment

`hybrid_review.py` combines fixture authorization/current-version
filtering, BM25, local vector ranking and reciprocal-rank fusion. It obtains
a second fixture snapshot to recheck candidates, rejecting duplicate authorized
IDs, conflicting current versions within the authorized fixture view, or changes
to selected passage content or metadata, and returns citation metadata
for human review rather than an answer or approval. The snapshot provider must
include current identity-dependent permissions and lifecycle state; this code
does not authenticate users. An empty or invalid candidate set, missing
metadata, model failure or revoked candidate returns unavailable.

The local `hybrid_review_probe.py` run ranked current Cedar v2 first and
excluded superseded v1 and the two unauthorized fixture passages. Its top
five also included an unrelated instruction-like passage. The current
prototype has no relevance cutoff or safe automated answerability check and
must not send arbitrary retrieved text to an LLM as trusted instructions.
The full local fixture suite passed 29 tests; GitHub CI runs unit tests and
a separate disposable PostgreSQL job,
not local model inference. This experiment does not connect to Phase 12/13
records, guarantee atomic authorization, create a real human review task, or
establish safe rendering or prompt-injection resistance.

## Phase 13-shaped evidence fixture

`phase13_snapshot_fixture.py` maps synthetic records shaped like Phase 13
version and extracted PDF evidence data to search fixtures with page, line and
source-hash metadata. It selects the highest numbered version per fixture
family and does not fall back to an older version when the newest job is
incomplete. Tests reject ambiguous versions, unverified fixture flags, missing
PDF citation locations, changed source hashes and changed line references.
The combined retrieval prototype compares supplied provenance across its two
fixture snapshots.

This is a format and policy experiment, not a database connector. Membership,
source verification and lifecycle values are synthetic caller assertions and
are not actually verified by this adapter. It only accepts fixture
selectable-text PDF evidence and intentionally excludes unversioned records;
it does not handle TXT, OCR, deletion or production lifecycle semantics.
The separate experimental `phase13_database_snapshot.py` bridges the Phase 13
draft database and store in a disposable synthetic test: it rechecks a
server-resolved principal using the draft membership logic, queries versioned
records in that tenant and calls the source hash check for the latest
completed version before creating fixture search passages. For synthetic
PDFs, it also re-extracts the field evidence with the existing bounded parser
and rejects a mismatch with the stored extraction. This is an exact
reproducibility check, not semantic entailment or a complete PDF sandbox.
A separate QA-only
lifecycle table marks synthetic sources active, withdrawn or deleted.
Missing lifecycle records fail closed, and withdrawal or deletion of the
newest version does not expose an older one. The test refuses to run unless
explicitly enabled and the database is on localhost with a
`nawa_phase13_qa_` name. Its result must be checked in GitHub CI.

This is not connected to a user-facing API or the running portal. The QA-only
table is not a production migration: its deletion marker does not delete
source files, erase embeddings or implement a retention policy. Deletion
and revocation of documents are not implemented in the Phase 13 schema.
An approved lifecycle policy, independent review and real browser identity
verification remain open. A snapshot recheck is not atomic with subsequent use.
Production retrieval and Phase 14 acceptance depend on the unresolved Phase
12/13 identity and lifecycle security boundaries.

The disposable database integration suite also exercises a successful
retrieval using actual Phase 13 synthetic PDF evidence. The citation includes
the source document ID, PDF page and extracted line, and source hash, while a
test spy checks that another tenant's source is not read. Additional tests
change a source, add a newer pending version, or remove its lifecycle state
during embedding, and require the result to become unavailable on recheck.
This uses fake
embeddings and the Phase 12 test membership implementation; it does not test
browser authentication, production file isolation, or an LLM answer.

## Synthetic citation resolution

`resolve_review_evidence.py` reloads an authorized synthetic snapshot before
returning a cited text line for human review. It checks the citation's source
ID, page, line, source hash and extracted-text hash against that snapshot.
Changed, revoked or missing evidence returns unavailable. In the disposable
PostgreSQL test the snapshot also rechecks synthetic membership and verifies
source bytes. The text is explicitly labeled untrusted and no approval is
issued.

The citation object is not signed or bound to a persisted review task, and
the experimental function is not an authenticated endpoint. It does not
provide safe HTML rendering, prevent a change after the final check, prove
semantic support, or prevent prompt injection. Production use requires a
reviewed authorization and evidence-handling design.

