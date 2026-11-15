# Phase 10 - Dockerized local portfolio demo

**Scope:** Synthetic quotation demonstration for a single user on a trusted office or personal machine. This is not a production service, a secure multiuser system, or a public demo URL.

## Prerequisites

- Docker Desktop with Linux containers enabled (or Docker Engine with Compose V2).
- Appropriate company/IT authorization to install and run Docker Desktop at work.
- Access to this GitHub repository and internet access to download the Python base image/dependency on first build.
- **Windows office PC:** compatible Windows 10/11, WSL 2 where applicable, CPU virtualization enabled, at least 8 GB RAM (see current Docker Desktop requirements).
- **Mac:** supported macOS release; recent Docker Desktop does not support old macOS 12. The project still runs via `python3 -m nawa_demo.dashboard` on an older Mac.

Docker Desktop commercial licensing is separate from NAWA's MIT/other project licensing and may require a paid subscription at larger organizations. Consult IT and Docker's current licensing terms.

## Clone and start on Windows (PowerShell)

```powershell
git clone https://github.com/zenithdevelopers7-source/nawa-document-intelligence.git
cd nawa-document-intelligence
docker --version
docker compose version
docker compose up --build -d
docker compose ps
```

Open http://127.0.0.1:8765 in the **office computer's own browser**. This is not accessible on another machine, since Compose binds to the host loopback address. To inspect logs:

```powershell
docker compose logs --tail=50 nawa
```

Stop and remove the container with `docker compose down`. Restart with `docker compose up -d`. Do not run `docker compose down -v` for this stateless example; there are no volumes.

## Start on a supported Mac/Linux computer

```bash
git clone https://github.com/zenithdevelopers7-source/nawa-document-intelligence.git
cd nawa-document-intelligence
docker compose up --build -d
docker compose ps
```

If the repo is already cloned, `git pull --ff-only` from its root instead of cloning again.

## Demo walkthrough

1. Load the bundled English quotation and Arabic quotation.
2. Inspect supplier details, VAT calculation and source evidence.
3. Compare both and observe the lower synthetic valid total.
4. Load the incorrect VAT quotation; confirm its invalid calculation is excluded from valid ranking.
5. Start a review for a valid sample and approve or request changes with a synthetic reviewer ID.
6. Stop the container and restart it: in-memory demo state should reset (intentional).

## Technical design and security notes

- Docker `dashboard_container` binds `0.0.0.0` **inside the container** for Docker port forwarding. Compose publishes **only** `127.0.0.1:8765` on the host. Never change the published address to `0.0.0.0` or forward to LAN/internet.
- Existing local Mac command remains `python3 -m nawa_demo.dashboard` with its original `127.0.0.1` binding.
- Runtime uses an unprivileged container account, a read-only filesystem, a memory-backed `/tmp`, dropped Linux capabilities, and `no-new-privileges`.
- Does not upload data to external providers, but Docker base images and Python packages download during the build. The application itself is an HTTP demo with no login. Do not upload sensitive, customer, or real supplier information.
- Reviews and uploads are stored only in memory. Container restarts reset data. No database, backups, authentication, authorization, persistent audit logs, CSRF token, external security audit or production deployment.
- Fixed browser Origin validation in Phase 9 is `http://127.0.0.1:8765`; use that exact URL and port. `localhost` may not match.
- Uses selectable-text PDF extraction; OCR is not enabled in the web interface.
- CI builds the image and does simple HTTP/sample-loading smoke checks. CI does not prove all host-specific Docker Desktop conditions or enterprise deployment readiness.

## Testing

Existing GitHub Actions runs the Python test suite. A separate `docker-smoke.yml` workflow builds the image and checks health, the HTML page, and sample loading on a temporary runner. Locally, run `python3 -m unittest discover -s tests -v` inside `demo/` when Python/PyMuPDF are installed.
