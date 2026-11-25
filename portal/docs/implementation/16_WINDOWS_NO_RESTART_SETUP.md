# v0.4.2 — Windows setup without restarting Windows

## Review scope

The user's RAR could not be downloaded: the file-transfer tool rejects archives
larger than 32 MiB. Its contents and any user-only modifications were not inspected.
This review covers the generated complete source available in the shared workspace,
the previous release archives, and the user's supplied terminal logs. It does not
claim an exhaustive security audit or that every production roadmap phase is done.

## Findings and fixes

1. Broad version replacement corrupted five dependency records. The v0.4.1 repair
   remains included, and release metadata changes use the structural updater.
2. npm ci tried replacing esbuild/Rollup binaries while older processes held them.
   New `stop` and `setup --stop-running` select only recognised project-owned
   Vite, esbuild and API processes. No blanket `taskkill /IM node.exe` is used.
3. npm.cmd added an unnecessary shell layer. The launcher now starts Vite's Node
   entry point directly and retains its process handle.
4. On Windows, a kill-on-close Job Object owns the launched API/Vite children.
   Closing/crashing the launcher closes that job and terminates its owned children.
   Assignment failures cancel startup and run the cleanup path.
5. A hidden npm lockfile could survive a failed setup and incorrectly suggest
   readiness. A manifest-hash marker is now written only after successful install,
   settings validation, migration and build. Missing/stale markers block run.
6. Concurrent setup/run could damage dependencies. A process-held OS file lock
   prevents concurrent operations; leftover lock files do not block new processes.
7. Windows native file replacement is checked before installation. If a file is
   still blocked by another app or permissions, setup fails before npm changes it.
8. Cursor tasks now use available ports; the Windows setup task stops this project's
   recognised processes first. Startup no longer clears earlier terminal output.
9. Source packaging excludes RAR/7z files and runtime logs as well as dependencies,
   configuration and saved data. A previously copied RAR cannot bloat the source ZIP.

## Existing v0.4.x installation: use the small update ZIP

1. Back up any source files you edited. The supplied RAR was not inspected, so
   do not assume a custom change exists in the replacement package.
2. Extract `UAE-Sovereign-Agentic-AI-Windows-Setup-Update-v0.4.2.zip` INTO the existing
   `nawa-workspace`, merging folders and replacing its included source files.
   It does not include `.env`, `.data`, `.venv` or node_modules.
3. Open PowerShell and paste:

```powershell
Set-Location "C:\UAE-Sovereign-Agentic-AI\nawa-workspace"
py -3.12 nawa.py setup --stop-running
if ($LASTEXITCODE -eq 0) {
    py -3.12 nawa.py run --auto-ports
}
```

No Windows reboot is part of this procedure. The stop action terminates recognised
local project services; save any unfinished form inputs first. Persisted records
and configuration are not deleted. Wait for SETUP COMPLETE, then READY; keep the
launcher terminal running. The new version requires one successful setup to write
its readiness marker, even if node_modules already existed.

`py -3.12 nawa.py stop` is also available independently. It refuses production
configuration and never kills Cursor/Chrome or an unrelated Node project by name.
Process creation time and executable are checked again on a held Windows process
handle, protecting against a reused PID. Relative/ambiguous process paths are not
stopped automatically. The stop implementation on non-Windows advises Ctrl+C;
Unix launcher cleanup still uses its own process groups.

## If a file remains blocked

The tool cannot terminate an unrecognised application or override access controls.
Close the specific terminal/application holding the file and retry. Alternatively,
extract the full source ZIP into a NEW folder and install there: it has no old
node_modules to unlock. To move persisted SQLite data, stop the old service first,
back up/copy .env and .data, preserve any absolute DATA_DIR/DATABASE_URL settings,
and do not copy virtual environments or node_modules. No reboot is required by
that clean-folder path. Antivirus or access-policy issues may still need their
actual diagnosis; do not disable protection or assume Administrator is necessary.

## Validation evidence

- 86 tests passed and 1 skipped in Linux. New tests cover ownership boundaries,
  unrelated projects, unicode paths, PID reuse, operation locks, stale readiness
  markers, failed install, preflight ordering and production-stop refusal.
- The skipped test specifically exercises a native Windows Job Object. It is
  included for Windows CI; no native Windows execution is claimed in this session.
- Full setup executed: locked pip, clean npm ci (115 packages), settings,
  migrations, TypeScript and production build passed.
- Real launcher reached readiness. A second setup refused before installing.
- Readiness/sign-in/cited search/create/compare/independent review smoke passed.
- Quotation source review, unknown fields, nested dialog and mobile browser checks
  passed under the direct-Vite launcher.
- Ctrl+C released both API/frontend ports; remaining checks and formatting passed.

## Sharing a reviewable source archive

From the project root run `py -3.12 scripts/package_source.py`. The resulting
artifacts source ZIP excludes .env, runtime data, dependencies and nested archives.
Review it before sharing. The generated complete source package is about 11 MiB,
within the file-transfer limit. This is preferable to a RAR of an installed folder.
