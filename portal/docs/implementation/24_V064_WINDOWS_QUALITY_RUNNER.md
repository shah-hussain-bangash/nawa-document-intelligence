# v0.6.4 — Windows UTF-8 quality runner

The user's benchmark stopped before processing questions: pathlib.read_text used
Windows cp1252 to read the UTF-8 English/Arabic dataset. The runner now specifies
utf-8-sig explicitly, accepting UTF-8 with or without a BOM. It no longer depends
on the terminal's default encoding or requires Python -X utf8 for dataset input.

## Apply the v0.6.3 update

Stop the app with Ctrl+C in the terminal showing READY. Keep Ollama running.
Extract Nawa_Windows_Quality_Fix_v0.6.4.zip and copy BOTH items beside nawa.py:

- apply_quality_fix_v064.py
- quality_fix_v064/

The updater checks every listed base hash before source writes, saves old source
in .data/update-backups, and refuses customized targets or an active launcher.
Config, saved cases, documents and retrieval.py are not payload targets.

```powershell
py -3.12 apply_quality_fix_v064.py
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py quality --output "artifacts/quality-hybrid.json"
}
```

The new quality command uses the existing .venv interpreter and shared .env loader,
including backend import paths. No dependency installation or migration is needed
to run it. The normal setup/build procedure remains necessary before starting
the updated frontend after release metadata changes.

If the command says the project is running, stop its actual launcher terminal
with Ctrl+C. The Windows helper `py -3.12 nawa.py stop` can stop recognised project
processes; wait for the launcher terminal to finish before applying a source update.

## First embedding-model load and OCR paths

In the same terminal, refresh saved executable paths if needed:

```powershell
$env:Path = [Environment]::ExpandEnvironmentVariables(
    ([Environment]::GetEnvironmentVariable("Path","Machine"),
     [Environment]::GetEnvironmentVariable("Path","User"),
     $env:Path) -join ";"
)
$env:Path = "$env:ProgramFiles\Tesseract-OCR;$env:LOCALAPPDATA\Microsoft\WinGet\Links;$env:Path"
```

The user has already verified embeddinggemma:300m returns two 768-dimensional
vectors. If idle model loading needs extra time, warm it before the benchmark:

```powershell
$warmupBody = @{model="embeddinggemma:300m"; input=@("Synthetic evaluation warmup")} | ConvertTo-Json
$warmup = Invoke-RestMethod -Uri "http://127.0.0.1:11434/v1/embeddings" -Method Post -ContentType "application/json" -Body $warmupBody -TimeoutSec 120
py -3.12 nawa.py quality --output "artifacts/quality-hybrid.json"
```

RETRIEVAL_MODE=hybrid and EMBEDDING_MODEL=embeddinggemma:300m must remain in the
local .env for the hybrid run. The runner prints its selected retrieval mode.
Keep configuration private; the generated report contains synthetic fixture results.

## What the report measures

The command creates a temporary database and synthetic corpus. It does not use
or reset the active workspace database. The fixture set contains 100 questions:
50 English and 50 Arabic, with 80 answerable and 20 unsupported questions.
Progress is printed every ten questions; the temporary engine is disposed even
when a search/embedding request fails, before Windows directory cleanup.

Recall@4 asks whether the expected title appears among the first four candidates;
MRR measures its rank. The retained unanswerable_abstention_rate JSON key measures
an empty retrieval candidate set on unsupported questions. The report now states
this scope, and console output calls it candidate-empty rate. This does not measure
the final-answer field guard that withheld the bank-account answer in the UI test.

OCR field scores cover the six labelled fields in each bundled scanned fixture,
before human correction. Ready status alone does not establish field accuracy.
These developer-authored fixtures are not independently reviewed held-out data.
Low scores remain visible. No real hybrid quality improvement or production
acceptance is claimed before the user's report is collected and reviewed.

## Verification

Legacy-default subprocess test runs all 100 questions with Python UTF-8 mode
disabled. Other tests check DB closure before temporary cleanup on search failure
and quality-command .env/output forwarding. A real lexical CLI run and OCR sample
evaluation provide a retained baseline in verification/v064/quality-lexical.json.
