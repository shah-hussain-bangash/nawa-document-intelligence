# v0.4.1 — Repair frontend dependency lock

The v0.4.0 setup log showed `npm error Invalid Version: 0.4.03`. Application
startup succeeded only because older installed node_modules were still present;
that did not prove setup succeeded.

Cause: a broad release-version string replacement accidentally modified five
transitive dependency records, including versions, URLs and dependency ranges.
Earlier v0.3.1 also modified @standard-schema/utils. All dependency records are
restored from the previously clean-installed v0.1.1 lock, preserving application
release metadata and original integrity hashes. No dependency upgrade is intended.

The exact corrected entries are @babel/generator's gen-mapping range,
@jridgewell/gen-mapping 0.3.13, @reduxjs/toolkit's utils range,
@standard-schema/utils 0.3.0 and immer 10.2.0.

## Repair an existing installation

Stop the launcher with Ctrl+C. Run from the folder containing nawa.py.
The repair utility `scripts/repair_frontend_lock.py` backs up the old lock once,
restores the five dependency records, and preserves release/configuration/data.
Then run setup. Start the application only if setup exits successfully.

```powershell
py -3.12 scripts/repair_frontend_lock.py
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py setup
    if ($LASTEXITCODE -eq 0) {
        py -3.12 nawa.py run --auto-ports
    }
}
```

The small `UAE-Sovereign-Agentic-AI-Frontend-Lock-Repair.zip` contains only that
utility and these instructions. Merge its scripts folder into the existing
nawa-workspace. Configuration, database and runtime data are not in the archive.
Alternatively the complete v0.4.1 source ZIP includes the corrected lock.
Do not remove .env, .data or the Python virtual environment for this fix.

## Prevention and validation

Use `python scripts/set_version.py X.Y.Z` for future releases. It assigns only
root JSON release fields and anchored Python/TOML release metadata. It never
performs a global substitution in dependency content.

Regression tests verify every dependency record survives a 0.3.1 → 0.4.0 release
bump unchanged, the repair restores the whole expected lock, and repeat repair
preserves the first backup. A clean npm ci in an isolated temporary folder
installs 115 packages; the build runs against those freshly installed packages.
Native Windows execution is not claimed; this repair addresses the exact npm
metadata defect observed in the user's Windows log.
