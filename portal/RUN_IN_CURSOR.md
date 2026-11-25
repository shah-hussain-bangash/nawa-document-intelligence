# Current update — v0.6.1

Existing v0.6.0 users: see `docs/implementation/21_V061_FIELD_GROUNDING.md` for the
small source-only updater and exact commands. Stop the app first. Runtime config,
database and uploads are not update targets. The updater checks expected source
hashes, backs up old source and refuses custom source changes. No new dependency
or schema is introduced. A full source release is also available for a new folder.

# UAE Sovereign Agentic AI v0.6.0 — current instructions

Read `docs/implementation/20_V060_OCR_HYBRID_AND_RECOVERY.md` first. This is a
complete-source upgrade, including backend, frontend, migration, OCR data and
worker. Stop the old app; back up config/data; use a NEW extracted folder. Copy
only `.env` and `.data` after stopping the old application. Inspect absolute DB/
data paths. Do not run old/new code against the same database or copy old venv/
node_modules. No Windows restart is required.

Open the new folder containing `nawa.py` in Cursor, then run:

```powershell
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

The default needs no paid model key. Native scanned-PDF OCR needs Tesseract and
Poppler; the included Docker image contains them. TXT/text PDFs still work without
system OCR tools. Optional hybrid/model/identity setup and actual verification
limits are in guide 20. All 26 production acceptance gates are NOT claimed closed.

---

# Historical setup notes (v0.5.0 and earlier)

These notes are retained for prior-release troubleshooting; guide 20 takes
precedence for the current release.

# UAE Sovereign Agentic AI v0.5.0

Use the COMPLETE source ZIP: frontend + backend + migration are required.
Start with `docs/implementation/17_V050_EVIDENCE_HISTORY.md` for the safe upgrade
and walkthrough, then `18_PHASE_COMPLETION_STATUS.md` for all 26 phase statuses.

Stop the old server and back up .env/.data/custom source. Extract v0.5 into a new
folder and move config/data only after stopping the old service. Do not copy
virtual environments or node_modules. Then:

```powershell
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

Wait for SETUP COMPLETE then READY, open the printed URL and leave PowerShell
running. Setup backs up an existing versioned SQLite DB before upgrading its
schema. Original uploads still need inclusion in your own full-data backup.
No reboot or paid model key is required by the local workflow.

# v0.4.2 — No-restart Windows setup

Existing v0.4 users: merge the Windows Setup Update ZIP into the workspace.
Preserve .env/.data and any customised source files. Then run from the workspace:

```powershell
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

Read `docs/implementation/16_WINDOWS_NO_RESTART_SETUP.md` for stop behaviour,
verification limits and clean-folder fallback. No reboot is part of the procedure.

# v0.4.1 setup correction

If npm reported Invalid Version: 0.4.03, follow
`docs/implementation/15_FRONTEND_LOCK_REPAIR.md`. Do not start the app after a
failed setup; run only once SETUP COMPLETE has appeared and exit status is zero.

# UAE Sovereign Agentic AI — v0.4 functional release

This release needs BOTH backend and frontend. Use the complete source ZIP.
Existing users: follow `docs/implementation/13_STEP_01_QUOTATION_DRAFTS.md` for
a data-preserving upgrade into a new folder. Do not apply an older UI-only ZIP.

In the new/extracted nawa-workspace:
`py -3.12 nawa.py setup`, then `py -3.12 nawa.py run --auto-ports`.

# UAE Sovereign Agentic AI — v0.3 Navy & Gold

Existing v0.2 users can apply the small UI-only update without reinstalling.
See `docs/implementation/11_NAVY_GOLD_UI.md` for exact merge instructions.

Full-source installations: `py -3.12 nawa.py setup`, then
`py -3.12 nawa.py run --auto-ports`. Keep PowerShell running and open READY URL.

# UAE Sovereign Agentic AI — v0.2 redesign

New installation: `py -3.12 nawa.py setup`, then `py -3.12 nawa.py run --auto-ports`.
Open the READY URL and keep the terminal running. Ctrl+C stops both services.

Upgrading from v0.1: follow `docs/implementation/08_UAE_UI_AND_GAP_REVIEW.md`.
Preserve `.env` and `.data`; do not overwrite your existing project or delete data.

# Open and run Nawa in Cursor — v0.1.2

The v0.1.2 lockfiles include the Windows-only tzdata/colorama dependencies.
For a v0.1.1 install with a tzdata hash error, see
`docs/implementation/07_WINDOWS_LOCK_FIX.md`; do not disable hash checking.

## 1. Extract and open the correct folder

Download the latest `Nawa_Cursor_Ready_v0.1.2.zip` and extract it. In Cursor choose
**File → Open Folder** and select the extracted **nawa-workspace** folder containing
`nawa.py`, `pyproject.toml`, `apps/` and `backend/`. Alternatively open
`nawa.code-workspace`. Do not open the ZIP itself or only `apps/web` as the project.
You do not need to upload the source to an external website.

When Cursor asks whether to trust this code, review the included files and choose
according to your local policy. Recommended extensions are listed; the Python
and debugger extensions are needed only for editor test/debug integration.

## 2. Prerequisites

- **Python 3.12** is the verified runtime; tooling also accepts Python 3.13.
- **Node.js 22.12+ or 24 LTS**, including npm 10+.
- Internet access to approved Python/npm registries during initial installation.
- Docker Desktop is optional; not required for the default local workflow.

Install missing runtimes from their official distributors, then restart Cursor so
its terminal can see them. No language-model API key is required to start.

## 3. Windows: run in Cursor's terminal

Open **Terminal → New Terminal**, at the extracted project root:

```powershell
py -3.12 --version
node --version
npm.cmd --version
py -3.12 nawa.py setup
py -3.12 nawa.py run
```

If your Python installation uses `python` rather than the `py` launcher, first
confirm `python --version` reports 3.12, then use `python nawa.py setup` and
`python nawa.py run`. The commands invoke virtual-environment Python and npm.cmd
directly; you do not need to activate a PowerShell script or change execution policy.

## 4. macOS / Linux: run in Cursor's terminal

```bash
python3 --version
node --version
npm --version
python3 nawa.py setup
python3 nawa.py run
```

On a machine with several Python versions, use `python3.12` instead of `python3`.
Some Linux distributions package the standard `venv`/`ensurepip` module separately;
install the matching Python venv package if environment creation reports it missing.

## 5. What setup and run actually do

`setup` creates an isolated `.venv`, installs hash-locked Python dependencies,
installs frontend dependencies with `npm ci`, preserves/initialises `.env`, creates
required local data directories, applies versioned database migrations and checks
the TypeScript/production build. It stops on failure instead of claiming success.
It does not download a model, purchase a service or provision cloud infrastructure.

`run` checks the environment and ports, starts FastAPI and Vite on loopback,
configures the proxy/origin consistently, and waits for both direct and proxied
API readiness. First application startup seeds synthetic fixtures idempotently.

Wait for **READY: http://localhost:5173**, then open that address on the same
computer. Keep the terminal running. Stop with **Ctrl+C**; saved records remain.
The application must be opened through its server, not by double-clicking index.html.

## 6. Verify from a second terminal

Windows:

```powershell
py -3.12 nawa.py doctor
py -3.12 nawa.py smoke
py -3.12 nawa.py smoke --workflow
```

macOS/Linux:

```bash
python3 nawa.py doctor
python3 nawa.py smoke
python3 nawa.py smoke --workflow
```

`doctor` reports prerequisites without showing secret values. `smoke` checks
readiness, local sign-in, the scoped workspace and real source citations.
`smoke --workflow` additionally creates one clearly labelled synthetic case, runs
its comparison and records an independent reviewed simulation. It retains that
sample for inspection. It sends no payments, supplier emails or real awards.

To run regression tests, a fresh migration check and the frontend build/formatting:

```bash
python3 nawa.py check
```

Use `py -3.12` on Windows. Existing application data and .env are not reset by check.

## 7. Cursor tasks and debugging

Choose **Terminal → Run Task**:

1. `Nawa: 1. Install and prepare`
2. `Nawa: 2. Run workspace`
3. `Nawa: Diagnose setup` or `Nawa: Verify running workspace`
4. `Nawa: Check tests and build`

Tasks use `py -3.12` on Windows and `python3` on macOS/Linux. If your system uses
another interpreter command, use the equivalent terminal commands above or update
the task command. In **Python: Select Interpreter**, choose this folder's `.venv`.

The API debug configuration starts only the backend. Stop the normal launcher
first, then start the frontend separately with `cd apps/web` and `npm run dev` if
you need browser + API debugging. Do not start two API processes on port 8000.

## 8. If the default ports are busy

The launcher never kills another program and Vite cannot silently move ports.
Use a different pair, then verify the matching web address:

```bash
python3 nawa.py run --api-port 8001 --web-port 5174
python3 nawa.py smoke --url http://localhost:5174 --workflow
```

Run the second command in another terminal. Use `py -3.12` on Windows.
The selected web origin and API proxy are configured together.

## 9. Optional PostgreSQL/Docker route

With Docker/Compose running:

```bash
python3 scripts/init-env.py
docker compose up -d --build
python3 nawa.py smoke --url http://localhost:8080 --workflow
```

Open http://localhost:8080. Here Python is only needed for initialisation/smoke;
the application runs in containers. The normal local route uses SQLite and does
not require a manually installed PostgreSQL, Redis or cloud account.
`docker compose down` stops containers; avoid `-v` unless you intend to delete data.
Managed cloud builds may need the approved CA/proxy override described in README.

## 10. Common problems

| Symptom | Action |
|---|---|
| Python/Node command not found | Install the recommended runtime and restart Cursor. |
| Node version unsupported | Use Node 22.12+ or 24 LTS, then rerun setup. |
| Missing packages or frontend | Run setup at the folder containing nawa.py. |
| Port occupied | Stop your other process or use the matched alternative-port command. |
| Connection refused | Keep run active and wait for READY; inspect the failed service output. |
| Proxy/certificate install failure | Correct the approved proxy/CA configuration; keep TLS/hash verification on. |
| An unversioned older database exists | Back up first, then run the explicit schema-adoption command in the operations guide. Do not delete .data to hide the problem. |
| PowerShell script restriction | Use py -3.12 nawa.py commands; no Activate.ps1 or npm.ps1 is required. |
| Scanned PDF has no text | This reference flags needs_ocr; OCR is a documented extension. |
| Browser-test Chromium missing | Run setup --browser, or provide an existing Chromium executable. |

## 11. First UI journey and scope

Enter as **Analyst → Emirates Operations**, open a draft case and run comparison.
Sign out and enter as **Reviewer** to decide independently. Search the knowledge
assistant and open the actual cited source. Try the Research Lab tenant to see
isolated records. Select Arabic for localised navigation/controls and RTL layout.

This is the complete source for the documented runnable sandbox. OCR/semantic RAG,
managed storage/queues, full Arabic copy and verified live cloud/model/identity
operation remain explicit extensions in `01_DOCUMENT_MAP.md` and the operations
guide. Installing into Cursor does not complete those integrations or certify
security/compliance. Windows/macOS adaptations are included; actual platform test
results are distinguished in the v0.1.2 validation report.
