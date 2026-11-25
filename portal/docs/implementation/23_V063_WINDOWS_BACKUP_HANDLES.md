# v0.6.3 — Windows backup/restore handle correction

## What failed

After setup successfully stopped the user's app, the backup command failed with
WinError 32 while deleting its temporary database.sqlite3. Python's SQLite
connection context manager commits/rolls back transactions but does not close the
connection. The snapshot was still open when TemporaryDirectory attempted cleanup.
Restore used the same pattern before renaming its validated temporary folder.

Both paths now use contextlib.closing for deterministic connection lifetime,
including errors and failure to open the destination connection. This retains
SQLite's consistent backup API and the existing manifest/restore validation.
No settings, upload, approval record, dependency or DB schema changes are required.

The old command copied its destination ZIP before cleanup failed. That attempt
may have left a ZIP on disk, but its nonzero exit also skipped the separate .env
copy. Keep existing files and retry with a new timestamp; do not rely on the
failed attempt until an archive is independently restored and checked.

## Apply the small v0.6.2 update

Extract Nawa_Windows_Backup_Fix_v0.6.3.zip. Copy both items beside nawa.py:

- apply_backup_fix_v063.py
- backup_fix_v063/

Stop the application's running terminal with Ctrl+C. The updater checks all
listed source hashes before changing any source, refuses an active normal
launcher/customized targets and backs up old source in .data/update-backups.
It does not target .env, database files, original uploads, parser.py or retrieval.py.

Run from the existing project folder after the app has stopped:

```powershell
Set-Location "C:\UAE-Sovereign-Agentic-AI\nawa-workspace" -ErrorAction Stop
py -3.12 apply_backup_fix_v063.py
if ($LASTEXITCODE -eq 0) {
    $backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupFile = "C:\UAE-AI-Backups\bilingual-ocr-$backupStamp.zip"
    py -3.12 nawa.py backup $backupFile
    if ($LASTEXITCODE -eq 0) {
        Copy-Item -LiteralPath ".env" -Destination "C:\UAE-AI-Backups\bilingual-ocr-$backupStamp.env" -ErrorAction Stop
        Write-Host "Backup and configuration saved. Archive: $backupFile"
    }
}
```

No setup reinstall or reboot is needed to run this corrected backup command.
If an app is still running, stop its actual launcher terminal with Ctrl+C.
The existing Windows stop helper is `py -3.12 nawa.py stop`; allow the launcher
terminal to finish before retrying an operation requiring the project lock.
Do not bypass the lock or delete active runtime files.

## Verify into a new directory

After the successful backup above, in the same terminal:

```powershell
py -3.12 nawa.py restore $backupFile "C:\UAE-AI-Restore\verified-$backupStamp"
```

Expected: Verified restore created, without WinError 32. Restore validates archive
paths/size, per-file SHA-256/length, SQLite integrity and required schema queries,
then creates the new directory. Existing destinations are refused. This check
does not switch the running application's DB or overwrite its active data.
The restored database is database.sqlite3 and originals are in uploads/.
Config is kept separately. Later application-level recovery checks must confirm
roles, source versions, historical reports and case state against the restored DB.

The ZIP contains database/uploads, not .env/keys, source code or installed models.
Checksums detect corruption; the ZIP is not encrypted. Keep the backup and copied
configuration in your own access-controlled local storage.

## Test scope

Tests retain real SQLite connection references to expose leaks even when Linux
would permit deletion. Guards verify closure before temporary cleanup and folder
rename. Cases cover successful backup/restore, corrupt source DB, corrupt DB inside
a correctly hashed archive, and destination-open failure. Tests preserve source
bytes/uploads, ensure no destination is published on failure, and check cleanup.
These portable tests do not replace native Windows confirmation or production DR.
