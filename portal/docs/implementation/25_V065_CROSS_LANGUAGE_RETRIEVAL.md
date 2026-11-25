# v0.6.5 — Cross-language retrieval profile

## Measured problem

The user's v0.6.4 Windows hybrid report found 47/80 expected titles: all 40
same-language targets but only seven of 40 cross-language targets. The 360-input
diagnostic captured real vectors from local embeddinggemma:300m, 768 dimensions,
BF16, Ollama 0.40.15. Its source hashes and question-suite hash matched the release.
An offline replay reproduced the original 47/80 result exactly.

The 0.45 cosine cutoff excluded many cross-language matches. Raw query/body inputs
also omitted the model's asymmetric retrieval format. Flat fusion could crowd a
strong semantic-only source out behind weaker lexical+dense overlaps.

## Implemented profile

- EmbeddingGemma queries use `task: search result | query: ...` and documents use
  `title: ... | text: ...`. Original citation text is retained. Other model names
  keep their existing raw-input profile.
- The strongest two distinct semantic source heads are preserved before filling
  the four-result list by reciprocal rank fusion.
- With no lexical match, weak dense matches whose best distinct-source margin is
  below 0.02 are withheld when the best score is within 0.10 above the cutoff.
  Overlapping pages/chunks of one document do not count as distinct alternatives.
- Bounded source-language phrases such as "Arabic procurement guide", "English
  policy" or "السياسة باللغة الإنجليزية" narrow the already permitted source set.
  Query language alone does not impose a source-language restriction. Comparisons
  mentioning both languages retain both. Strong page-script evidence can correct
  a stale filename-based language label for selection; stored metadata is unchanged.
- Field evidence checks receive this scoped source set. Existing ACL, status,
  classification, route, version and capacity boundaries remain in place.

Publisher reference for the original model's retrieval formats:
https://github.com/google-gemma/cookbook/blob/main/.archive/Gemma/%5BGemma_3%5DRAG_with_EmbeddingGemma.ipynb

Source-language phrases are bounded rules, not general language understanding or
a full language classifier. This profile does not implement policy effective dates,
table extraction, a persistent vector index or general factual entailment.

## Apply from v0.6.4

Stop the app with Ctrl+C in its READY terminal. Keep Ollama running. Extract
Nawa_Hybrid_Ranking_Fix_v0.6.5.zip and copy BOTH items beside nawa.py:

- apply_ranking_fix_v065.py
- ranking_fix_v065/

The updater checks listed base hashes before source writes, saves previous source,
and refuses customized targets or an active launcher. It does not target .env,
saved records or uploads. The captured baseline hashes matched the retrieval and
embedding files; later local changes still require review if an update is refused.

In the existing .env replace the current cutoff line with:

```dotenv
RETRIEVAL_MIN_COSINE=0.25
```

Keep the other configured hybrid settings, including embeddinggemma:300m and the
synthetic classification. The generic Settings default remains 0.45; this measured
Gemma profile requires the explicit .env edit. A cosine is not a probability or
procurement eligibility score. Other models/corpora require their own evaluation.

```powershell
py -3.12 apply_ranking_fix_v065.py
if ($LASTEXITCODE -eq 0) {
    $warmupBody = @{model="embeddinggemma:300m"; input=@("Synthetic evaluation warmup")} | ConvertTo-Json
    $warmup = Invoke-RestMethod -Uri "http://127.0.0.1:11434/v1/embeddings" -Method Post -ContentType "application/json" -Body $warmupBody -TimeoutSec 120 -ErrorAction Stop
    py -3.12 nawa.py quality --output "artifacts/quality-hybrid-v065.json"
}
```

Confirm the output says hybrid, profile embeddinggemma-retrieval-v1 and cutoff
0.25. The new output filename preserves the previous report. No dependency install
or schema migration is needed for quality; run normal setup/build before starting
the updated frontend. Keep the terminal PATH that passed OCR prerequisites, or
refresh saved PATH/Tesseract/WinGet paths as described in guide 24.

## Results and limits

| Replay configuration | Found / 80 | Unsupported empty / 20 |
|---|---:|---:|
| Original raw inputs, 0.45, RRF | 47 | 9 |
| Retrieval-formatted inputs, 0.45, RRF | 50 | 9 |
| Retrieval-formatted inputs, 0.25, RRF | 72 | 7 |
| Final profile plus explicit source-language requests, 0.25 | 76 | 9 |

Final captured-score replay: Recall@4 95%, same-language 40/40, cross-language
36/40, MRR 0.8302. All 47 prior supported hits remain. Q046, Q047, Q069 and Q071
remain missed. Labels are unchanged; alternate-source relevance still needs review.
The candidate-empty statistic is not final-answer grounding or hallucination rate.
The bank-account field guard remains separately tested. OCR fields are unchanged;
the sample's Arabic VAT and date still need manual review.

The compressed regression fixture stores captured query/passage cosine matrices
and model/source provenance, not model weights. Its replay tests post-embedding
ranking using those measured similarities. It does not execute the model's forward
pass. This calibration used the same developer-authored 100 cases, so it is not an
independent held-out result. Native Windows live rerun, broader precision/answer
quality and representative user acceptance remain required.
