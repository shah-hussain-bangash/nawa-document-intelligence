# Cursor-ready release v0.1.1

This release completes packaging and local startup usability gaps found during
review of the v0.1.0 source. It does not silently mark future enterprise roadmap
integrations complete.

## Completed fixes

- Added a portable root command: `python nawa.py setup/run/doctor/check/smoke`.
- Added Cursor workspace, recommended extensions, tasks, debugger settings,
  Python analysis paths, project rules and secret/runtime ignore rules.
- Added Windows/PowerShell and macOS/Linux instructions without requiring shell
  activation or changing PowerShell execution policy.
- Added runtime/dependency checks and explicit occupied-port diagnostics.
- Frontend uses a strict configured port; API proxy and allowed web origin change
  together for alternative port pairs.
- Startup reports READY only after direct and proxied dependency readiness; a
  failed child or timeout returns failure and cleans up the processes it started.
- Preserved configuration/data while additively generating a missing local
  database password. Added literal UTF-8/BOM-aware environment reading.
- Made Linux-only parser limits explicit and retained required Windows system
  variables in the minimal parser environment; parser secrets are not inherited.
- Browser tests discover system or Playwright-managed Chromium instead of assuming
  a Linux-only executable path. Sandbox disabling requires explicit opt-in except
  when already running as root in CI/container environments.
- Added startup-tool regression tests for failed subprocesses, ports, environment
  preservation, safe errors and remote smoke-target rejection.
- Added terminal verification of sign-in, citations and an optional full independent
  procurement review simulation. The optional workflow retains a clearly named
  synthetic verification case.

## Scope that still needs separate work

OCR, table extraction, semantic/pgvector retrieval, managed object storage/queues,
complete Arabic narrative translation, and live/cloud/operational identity/model
integrations remain the explicit extensions already recorded in the document map.
They are not required to run the delivered local sandbox and are not represented
as implemented merely because the project opens in Cursor.

Windows/macOS compatibility changes can be checked structurally and with isolated
tests here; actual Windows/macOS execution is not claimed without those systems.
