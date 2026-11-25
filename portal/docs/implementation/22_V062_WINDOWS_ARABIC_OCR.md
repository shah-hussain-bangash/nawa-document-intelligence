# v0.6.2 — Windows Arabic OCR update and retry

## Observed problem and fix

On the user's Windows installation, Tesseract and Poppler prerequisites passed.
The English scanned quotation reached Ready; the Arabic scan reached Failed with
zero saved pages. We reproduced that combination by running the actual parser
with PYTHONIOENCODING=cp1252: English exited 0, Arabic exited 1 with
UnicodeEncodeError before emitting a JSON result.

The parser used ensure_ascii=False. Redirected Windows stdout can use a legacy
encoding even with LANG=C.UTF-8. It now emits ASCII-escaped JSON; json.loads
restores the original Unicode. OCR text, evidence and document source bytes are
not converted to ASCII. The worker's UTF-8 reader accepts this portable wire format.
The screenshot alone cannot rule out other failures; verify the retry below.

## Existing v0.6.1 workspace

Download and extract Nawa_Windows_Arabic_OCR_Fix_v0.6.2.zip into the folder containing
nawa.py. It contains apply_arabic_ocr_fix_v062.py and arabic_ocr_fix_v062/.
Stop the running app with Ctrl+C first. The updater refuses a running launcher.
It checks all listed base hashes before changing source, backs up old source in
.data/update-backups and refuses customized targets. It does not target .env,
database files, uploads or retrieval.py. Do not force a rejected update.

Run in the existing PowerShell terminal that can find Tesseract and Poppler:

```powershell
Set-Location "C:\UAE-Sovereign-Agentic-AI\nawa-workspace" -ErrorAction Stop
py -3.12 apply_arabic_ocr_fix_v062.py
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py setup --stop-running
    if ($LASTEXITCODE -eq 0) {
        py -3.12 nawa.py services
        if ($LASTEXITCODE -eq 0) {
            py -3.12 nawa.py run --auto-ports
        }
    }
}
```

If a new terminal cannot find the already installed executables, refresh its PATH:

```powershell
$env:Path = ([Environment]::GetEnvironmentVariable("Path","Machine"), [Environment]::GetEnvironmentVariable("Path","User"), $env:Path) -join ";"
$tesseractDir = Join-Path $env:ProgramFiles "Tesseract-OCR"
if (Test-Path "$tesseractDir\tesseract.exe") {
    $env:Path = "$tesseractDir;$env:Path"
}
```

No Windows reboot is required. If OCR prerequisites still fail, run services and
inspect artifacts/service-validation.json locally before retrying. Model, identity
and embedding not_configured do not prevent default local OCR/extractive search.

## Retry the existing failed Arabic document

1. Open the READY URL and sign in as analyst Amira.
2. Documents -> scanned-quotation-ar.pdf -> Retry processing.
3. Wait for Ready and inspect the Arabic OCR text against the original scan.
4. If it still fails, report the new status and OCR capabilities output. Do not
   withdraw the existing source just to retry processing.

The English filename scanned-quotation-ar.pdf may still display English because
the current language label comes from upload metadata, not OCR language detection.
That label is not evidence of recognition quality. This patch does not implement
automatic language classification or arbitrary table extraction.

## Verification and limits

Regression tests use real parser subprocesses with forced cp1252, ASCII and UTF-8
stdout, preserve Arabic plus non-BMP Unicode TXT, and process the bundled real
English/Arabic scanned PDFs. A real API/worker test retries the same Arabic source
and checks its original download and version. These are Linux tests simulating
the affected Windows encoding; they do not constitute native Windows acceptance.
The full v0.6.2 archive includes the existing v0.6.1 grounding fixes. All 26 phase
acceptance gates remain tracked separately in guide 18.
