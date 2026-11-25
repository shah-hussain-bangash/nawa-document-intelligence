# Windows setup correction — v0.1.2

## Observed failure

The user's Windows/Python 3.12 setup reached dependency installation and failed:
`In --require-hashes mode ... tzdata ... must have their versions pinned with ==`.
Python and Node detection succeeded. Starting the application after this error
cannot work until dependency installation completes.

The supplied v0.1.1 requirements were compiled for the Linux host. psycopg has a
Windows-only tzdata dependency; pytest has a Windows-only colorama dependency.
Those were omitted. This was a packaging defect, not a reason to disable hash
checking, change expected checksums, reinstall Python or delete the user's data.

## Correction

Both lockfiles were regenerated with universal resolution and artifact hashes,
constraining existing versions to avoid unrelated upgrades. Windows tzdata 2026.6
is pinned and hashed in both locks; colorama 0.4.6 is in the development lock.
An emscripten-only httpx2-jsfetch pin is present under its own platform marker and
is not selected on Windows/Linux/macOS. Existing dependency versions are retained.
The advertised Python range is now explicit: 3.12 and 3.13.

## In-place repair for an existing v0.1.1 folder

`fixes/windows-lock-fix.ps1` adds the missing conditional pins and trusted hashes
only if absent. Its contents can be pasted into PowerShell without changing
execution policy. Then rerun `py -3.12 nawa.py setup`; once it reports SETUP COMPLETE,
run `py -3.12 nawa.py run`. Keep the space between `nawa.py` and the subcommand.
The incomplete virtual environment can be reused. `.env` and `.data` stay intact.

The complete corrected v0.1.2 ZIP already contains the universal locks; it does
not need the repair script. Extract into a new folder if trying it independently.

## Validation method and limits

The universal locks were projected onto Windows CPython 3.12 using PEP 508 markers.
Pip downloaded all 64 selected Windows wheels with `--require-hashes` and the
Windows wheel tags. This artifact-only download uses `--no-deps` deliberately;
an independent traversal of their actual wheel metadata then verifies all 94
applicable dependency relationships, including crypto/binary extras, have pinned
compatible versions. This avoids falsely treating a host-platform pip resolve
as a native Windows installation.

The source includes eight regression cases covering Windows 3.12/3.13 selection
and hash/pin completeness. Native Windows execution still requires its own result;
the GitHub CI template now includes Windows 3.12/3.13 installs and tests.

The expanded Linux regression suite passed all **49 tests**, followed by fresh
migration/schema checks, TypeScript/production build and formatting. Applying
the additive repair to the original v0.1.1 development lock was independently
checked against the same Windows wheel metadata; its dependency closure passed.

## Reproduce the cross-platform artifact check

From a development environment:

```bash
python scripts/validate_windows_lock.py export
python -m pip download --require-hashes --only-binary=:all: \
  --platform win_amd64 --python-version 3.12 --implementation cp --abi cp312 \
  --no-deps -r artifacts/windows-verified.requirements.txt \
  --dest artifacts/windows-wheels
python scripts/validate_windows_lock.py validate --wheels artifacts/windows-wheels
```

Installed dependencies and wheels remain excluded from the source archive.
