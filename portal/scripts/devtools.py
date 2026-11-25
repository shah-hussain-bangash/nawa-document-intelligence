"""Turnkey Cursor/local workflow with checked subprocesses and real readiness."""
import argparse
from datetime import date, timedelta
import http.cookiejar
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener
from uuid import uuid4
import venv

from scripts.local_config import initialise_env, local_environment
from scripts.process_control import (WindowsJob, check_windows_native_files, mark_frontend_ready,
    project_lock, require_frontend_ready, stop_windows_project)

ROOT = Path(__file__).resolve().parents[1]


def environment_python(root=ROOT):
    return root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def node_version():
    executable = shutil.which("node")
    if not executable:
        raise RuntimeError("Node.js is missing. Install Node.js 22.12+ or 24 LTS, restart Cursor, then retry.")
    version = subprocess.check_output([executable, "--version"], text=True).strip().lstrip("v")
    parts = tuple(int(part) for part in version.split(".")[:2])
    if not (parts[0] == 22 and parts[1] >= 12 or parts[0] == 24):
        raise RuntimeError("Use Node.js 22.12+ or 24 LTS for this tested Vite setup.")
    return version


def npm_executable():
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not executable:
        raise RuntimeError("npm is missing. Install the npm included with Node.js, restart Cursor, then retry.")
    return executable


def verify_python():
    if sys.version_info[:2] not in {(3, 12), (3, 13)}:
        raise RuntimeError("Use Python 3.12 (verified) or 3.13. On Windows: py -3.12 nawa.py setup.")


def checked(command, *, cwd=ROOT, env=None, label="Command"):
    print(f"\n{label}", flush=True)
    subprocess.run([str(part) for part in command], cwd=cwd, env=env, check=True)


def require_environment():
    python = environment_python()
    if not python.is_file():
        raise RuntimeError("Project environment is missing. Run: python nawa.py setup")
    return python


def dependency_probe(python):
    modules = ["fastapi", "uvicorn", "sqlalchemy", "alembic", "pypdf", "langgraph", "jwt"]
    probe = "import importlib.util,json;print(json.dumps([m for m in " + repr(modules) + " if importlib.util.find_spec(m) is None]))"
    result = subprocess.run([str(python), "-c", probe], capture_output=True, text=True, check=True)
    missing = json.loads(result.stdout)
    if missing:
        raise RuntimeError("Missing backend packages: " + ", ".join(missing) + ". Run python nawa.py setup.")


def setup(args):
    verify_python()
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}; Node {node_version()}", flush=True)
    npm = npm_executable()
    env = local_environment(ROOT)
    if env.get("APP_ENV", "local") not in {"local", "test"}:
        raise RuntimeError("Local setup refuses production mode. No dependencies or configuration were changed.")
    check_windows_native_files(ROOT)
    marker = ROOT / ".data/runtime/frontend-ready.json"
    marker.unlink(missing_ok=True)
    python = environment_python()
    if not python.exists():
        if (ROOT / ".venv").exists():
            raise RuntimeError("An incomplete .venv exists. Inspect/rename it before creating a replacement; no files were deleted.")
        print("Creating isolated .venv (existing data/configuration are preserved).", flush=True)
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
    checked([python, "-m", "pip", "install", "--require-hashes", "-r", ROOT / "requirements-dev.lock"], label="Installing hash-locked Python dependencies")
    checked([npm, "ci", "--no-audit", "--no-fund"], cwd=ROOT / "apps/web", label="Installing lockfile-controlled frontend dependencies")
    print(initialise_env(ROOT), flush=True)
    env = local_environment(ROOT)
    if env.get("APP_ENV", "local") not in {"local", "test"}:
        raise RuntimeError("This setup command is for local development; production configuration was preserved. Follow the deployment guide instead.")
    checked([python, "-c", "from uae_ai.core.config import Settings; Settings().validate()"], env=env, label="Validating local settings and creating required data directories")
    checked([python, "-c", "from uae_ai.core.config import Settings; from uae_ai.db import make_database; from uae_ai.core.migrations import migrate_local; s=Settings(); e,_=make_database(s.database_url); migrate_local(e,s.database_url); e.dispose()"], env=env, label="Backing up and applying versioned local database migrations")
    checked([npm, "run", "build"], cwd=ROOT / "apps/web", label="Checking TypeScript and production frontend build")
    if args.browser:
        checked([python, "-m", "playwright", "install", "chromium"], label="Installing optional Playwright Chromium")
    mark_frontend_ready(ROOT)
    print("\nSETUP COMPLETE. Run: python nawa.py run --auto-ports\nOpen the URL printed after READY; keep this terminal running.", flush=True)
    return 0


def port_is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        try:
            listener.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def doctor(args):
    verify_python()
    print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Node: {node_version()}; npm: available" if npm_executable() else "")
    dependency_probe(require_environment())
    print("Backend dependencies: installed")
    if not (ROOT / "apps/web/node_modules/.package-lock.json").is_file():
        raise RuntimeError("Frontend dependencies are missing; run python nawa.py setup.")
    require_frontend_ready(ROOT)
    print("Frontend dependencies: verified setup marker matches manifests")
    env = local_environment(ROOT)
    print("Local .env: present" if (ROOT / ".env").exists() else "Local .env: missing; run setup")
    print("Demo data/model: local mode requires no paid API credential.")
    for port in [args.api_port, args.web_port]:
        print(f"Port {port}: {'available' if port_is_free(port) else 'in use (expected if Nawa is already running)'}")
    print("DOCTOR COMPLETE. No secret values were displayed.")
    return 0


def readiness(api_port, web_port):
    # These are explicit loopback requests; outbound proxy settings stay intact.
    client = build_opener(ProxyHandler({}))
    for url in [f"http://127.0.0.1:{api_port}/health/ready", f"http://127.0.0.1:{web_port}/health/ready"]:
        try:
            with client.open(url, timeout=1) as response:
                if response.status != 200 or json.load(response).get("status") != "ready":
                    return False
        except (OSError, URLError, ValueError):
            return False
    return True


def stop_children(children):
    for _, process in children:
        try:
            if os.name == "nt":
                if process.poll() is None:
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for _, process in children:
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.wait(timeout=5)


def choose_available_ports(api_port, web_port):
    # Hold both reservations together so the OS cannot choose the same port twice.
    reservations = []
    try:
        result = []
        for preferred in (api_port, web_port):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            reservations.append(listener)
            try:
                listener.bind(("127.0.0.1", preferred))
            except OSError:
                listener.bind(("127.0.0.1", 0))
            result.append(listener.getsockname()[1])
        return tuple(result)
    finally:
        for listener in reservations:
            listener.close()


def run(args):
    python = require_environment()
    dependency_probe(python)
    node_version()
    npm = npm_executable()
    if not (ROOT / "apps/web/node_modules/.package-lock.json").is_file():
        raise RuntimeError("Frontend dependencies are missing. Run python nawa.py setup.")
    if getattr(args, "auto_ports", False):
        args.api_port, args.web_port = choose_available_ports(args.api_port, args.web_port)
        print(f"Selected API port {args.api_port}; web port {args.web_port}.", flush=True)
    if args.api_port == args.web_port:
        raise RuntimeError("API and web ports must differ.")
    for port in [args.api_port, args.web_port]:
        if not port_is_free(port):
            raise RuntimeError(f"Port {port} is already occupied. Stop its owner, or run with --auto-ports to select available ports. No other process was killed.")
    require_frontend_ready(ROOT)
    print(initialise_env(ROOT), flush=True)
    env = local_environment(ROOT)
    if env.get("APP_ENV", "local") not in {"local", "test"}:
        raise RuntimeError("The development launcher refuses production mode. Use the deployment runbook.")
    env.update(NAWA_API_PORT=str(args.api_port), NAWA_WEB_PORT=str(args.web_port), WEB_ORIGIN=f"http://localhost:{args.web_port}")
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    children = []
    job = WindowsJob()
    try:
        print("Starting API and frontend; waiting for database + proxied API readiness…", flush=True)
        children.append(("API", subprocess.Popen([str(python), "-m", "uvicorn", "uae_ai.main:app", "--host", "127.0.0.1", "--port", str(args.api_port)], cwd=ROOT, env=env, **options)))
        job.attach(children[-1][1])
        # Launch the long-lived Vite process directly, avoiding a detached npm.cmd shell.
        node = shutil.which("node")
        if not node:
            raise RuntimeError("Node.js is missing; startup was cancelled.")
        children.append(("Frontend", subprocess.Popen([node, str(ROOT / "apps/web/node_modules/vite/bin/vite.js"), "--host", "127.0.0.1", "--clearScreen", "false"], cwd=ROOT / "apps/web", env=env, **options)))
        job.attach(children[-1][1])
        deadline = time.monotonic() + args.timeout
        ready = False
        while True:
            for name, process in children:
                code = process.poll()
                if code is not None:
                    raise RuntimeError(f"{name} exited unexpectedly with code {code}; see its output above. Startup did not succeed.")
            if not ready:
                if readiness(args.api_port, args.web_port):
                    children.append(("Document worker", subprocess.Popen([str(python), "-m", "uae_ai.worker"], cwd=ROOT, env=env, **options)))
                    job.attach(children[-1][1])
                    print(f"\nREADY: http://localhost:{args.web_port}\nAPI docs: http://127.0.0.1:{args.api_port}/api/docs\nStop with Ctrl+C. Your data will be preserved.\n", flush=True)
                    ready = True
                elif time.monotonic() >= deadline:
                    raise RuntimeError("Startup timed out before both services were ready. Check the service output above and run python nawa.py doctor.")
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nStopping Nawa services; saved data is preserved.", flush=True)
        return 0
    finally:
        try:
            stop_children(children)
        finally:
            job.close()


def check(_args):
    python = require_environment()
    npm = npm_executable()
    with tempfile.TemporaryDirectory(prefix="nawa-check-") as temp:
        env = os.environ.copy()
        env.update(PYTHONPATH=str(ROOT / "backend/src"), APP_ENV="test", AUTH_MODE="demo", SEED_DEMO="true", MODEL_MODE="extractive", WEB_ORIGIN="http://localhost:5173", DATA_DIR=temp, DATABASE_URL=f"sqlite:///{Path(temp).as_posix()}/check.db")
        checked([python, "-m", "pytest", "-q"], env=env, label="Backend integration, security and startup-tool tests")
        checked([python, "-m", "alembic", "upgrade", "head"], env=env, label="Fresh database migration")
        checked([python, "-m", "alembic", "check"], env=env, label="Schema consistency")
    checked([npm, "run", "build"], cwd=ROOT / "apps/web", label="TypeScript + production frontend build")
    checked([npm, "run", "format:check"], cwd=ROOT / "apps/web", label="Frontend formatting")
    print("\nCHECKS PASSED. Your existing database and .env were not reset.", flush=True)
    return 0


def smoke(args):
    parsed = urlparse(args.url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise RuntimeError("Smoke verification is limited to a local http://localhost:PORT or http://127.0.0.1:PORT workspace.")
    base = args.url.rstrip("/")
    client = build_opener(ProxyHandler({}), HTTPCookieProcessor(http.cookiejar.CookieJar()))
    csrf = ""

    def request(path, data=None, extra_headers=None):
        body = json.dumps(data).encode() if data is not None else None
        headers = {"Content-Type": "application/json", "Origin": base}
        if csrf:
            headers["X-CSRF-Token"] = csrf
        headers.update(extra_headers or {})
        try:
            with client.open(Request(base + path, data=body, headers=headers), timeout=40) as response:
                payload = response.read()
                return json.loads(payload) if payload else None
        except HTTPError as exc:
            raise RuntimeError(f"Verification failed at {path} (HTTP {exc.code}); no credentials were printed.") from None

    assert request("/health/ready")["status"] == "ready", "Dependency readiness failed"
    if request("/auth/config")["mode"] != "demo":
        raise RuntimeError("The service is not in local demo mode. Verify OIDC through its real browser login; no demo access was attempted.")
    session = request("/auth/demo", {"role": "analyst", "tenant": "operations"})
    csrf = session["csrf"]
    try:
        workspace = request("/api/v1/workspace")
        assert workspace["tenant"]["id"] == "operations", "Tenant scope mismatch"
        answer = request("/api/v1/knowledge/query", {"question": "procurement quotations requirements"})
        assert answer["citations"], "No permitted source citations returned"
        print("PASS: readiness, sign-in, tenant workspace and cited evidence search.")
        if args.workflow:
            sources = [d for d in workspace["documents"] if d["status"] == "ready"]
            if not sources:
                raise RuntimeError("No ready evidence exists. Add authorised sample sources before workflow verification.")
            document_id = sources[0]["id"]
            case = request("/api/v1/cases", {"title": "Cursor startup verification " + uuid4().hex[:6], "description": "Synthetic end-to-end verification created by nawa.py smoke --workflow.", "department": "Digital Services", "budget": "10000.00", "due_date": (date.today()+timedelta(days=14)).isoformat(), "document_ids": [document_id], "quotes": [{"supplier": supplier, "amount": amount, "currency": "AED", "tax_percent": "5", "delivery_days": 14, "valid_until": (date.today()+timedelta(days=30)).isoformat(), "document_id": document_id} for supplier, amount in [("Verification Supplier A", "200.00"), ("Verification Supplier B", "300.00")]]})
            result = request(f'/api/v1/cases/{case["id"]}/runs', {}, {"Idempotency-Key": str(uuid4())})
            assert result["case"]["status"] == "awaiting_review", "Comparison did not reach review"
            request("/auth/logout", {})
            session = request("/auth/demo", {"role": "reviewer", "tenant": "operations"})
            csrf = session["csrf"]
            approval = result["case"]["approval"]
            decided = request(f'/api/v1/approvals/{approval["id"]}/decisions', {"expected_revision": result["case"]["revision"], "decision": "approve", "reason": "Verified the synthetic startup workflow and evidence-linked calculations."})
            assert decided["status"] == "approved_simulation", "Review outcome mismatch"
            print("PASS: create → compare → independent reviewer → approved simulation.")
            print("One clearly named synthetic verification case was retained for your inspection.")
        print("SMOKE VERIFICATION PASSED.")
        return 0
    finally:
        try:
            request("/auth/logout", {})
        except (RuntimeError, OSError):
            pass


def stop_local(_args):
    if local_environment(ROOT).get("APP_ENV", "local") not in {"local", "test"}:
        raise RuntimeError("Local stop refuses production configuration. No process was stopped.")
    stop_windows_project(ROOT)
    return 0


def bundle_backup(args):
    checked([require_environment(), "-m", "scripts.backup_workspace", "backup", args.destination], env=local_environment(ROOT), label="Backing up the stopped local database and original files")


def bundle_restore(args):
    checked([require_environment(), "-m", "scripts.backup_workspace", "restore", args.archive, args.destination], env=local_environment(ROOT), label="Verifying and restoring into a new directory")


def service_check(args):
    checked([require_environment(), "-m", "scripts.validate_services", "--output", args.output], env=local_environment(ROOT), label="Checking configured local services; secret values are never reported")


def quality_check(args):
    checked([require_environment(), "-m", "scripts.evaluate_quality", "--output", args.output], env=local_environment(ROOT), label="Evaluating 100 synthetic questions and OCR fixtures using local configuration")


def port_number(value):
    port = int(value)
    if not 1024 <= port <= 65535:
        raise argparse.ArgumentTypeError("Choose a local port between 1024 and 65535.")
    return port


def main(argv=None):
    parser = argparse.ArgumentParser(description="Nawa Cursor-ready local setup and run commands")
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("setup", help="Install locked dependencies, initialise config, migrate and build")
    install.add_argument("--browser", action="store_true", help="Also install optional Playwright Chromium")
    install.add_argument("--stop-running", action="store_true", help="Stop verified local project processes on Windows before setup; no reboot")
    install.set_defaults(action=setup)
    commands.add_parser("stop", help="Stop only this project's recognised Windows API/Vite/esbuild processes").set_defaults(action=stop_local)
    for name, handler in [("run", run), ("doctor", doctor)]:
        command = commands.add_parser(name)
        command.add_argument("--api-port", type=port_number, default=8000)
        command.add_argument("--web-port", type=port_number, default=5173)
        command.add_argument("--timeout", type=int, choices=range(5, 301), default=60, metavar="5..300")
        if name == "run":
            command.add_argument("--auto-ports", action="store_true", help="Select available ports without stopping other applications")
        command.set_defaults(action=handler)
    commands.add_parser("check", help="Test backend, migrations, frontend build and formatting").set_defaults(action=check)
    bundle = commands.add_parser("backup", help="Offline SQLite and original-file backup; stop the app first")
    bundle.add_argument("destination")
    bundle.set_defaults(action=bundle_backup)
    restore = commands.add_parser("restore", help="Validate a backup and restore into a new directory")
    restore.add_argument("archive")
    restore.add_argument("destination")
    restore.set_defaults(action=bundle_restore)
    services = commands.add_parser("services", help="Verify OCR and configured live identity/model/embedding endpoints")
    services.add_argument("--output", default="artifacts/service-validation.json")
    services.set_defaults(action=service_check)
    quality = commands.add_parser("quality", help="Evaluate synthetic English/Arabic retrieval and OCR fixtures using local .env")
    quality.add_argument("--output", default="artifacts/quality-report.json")
    quality.set_defaults(action=quality_check)
    verify = commands.add_parser("smoke", help="Verify an already-running local workspace")
    verify.add_argument("--url", default="http://localhost:5173")
    verify.add_argument("--workflow", action="store_true", help="Create and approve one clearly named synthetic verification case")
    verify.set_defaults(action=smoke)
    args = parser.parse_args(argv)
    try:
        if args.command == "setup" and args.stop_running:
            stop_local(args)
        if args.command in {"setup", "run", "backup", "restore"}:
            with project_lock(ROOT, timeout=8 if args.command == "setup" and args.stop_running else 0):
                return args.action(args)
        return args.action(args)
    except subprocess.CalledProcessError as exc:
        print(f"\nFAILED: a required command exited with code {exc.returncode}. Review its output above; no existing data was reset.", file=sys.stderr)
        return exc.returncode or 1
    except (RuntimeError, OSError, ValueError, AssertionError) as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        return 1

