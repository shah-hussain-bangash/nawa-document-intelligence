"""Create an ordered, secret-free source archive; excludes runtime state/dependencies."""
from pathlib import Path
import hashlib
import json
import zipfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "artifacts"
DEST.mkdir(exist_ok=True)
EXCLUDED = {".git", ".venv", ".venv-verify", ".data", "node_modules", "dist", "__pycache__", ".pytest_cache", "artifacts", "test-results", "playwright-report"}


def selected(path):
    relative = path.relative_to(ROOT)
    return (path.is_file() and not path.is_symlink()
            and not any(part in EXCLUDED or part.endswith(".egg-info") for part in relative.parts)
            and not (path.name == ".env" or path.name.startswith(".env.") and path.name != ".env.example")
            and path.suffix not in {".pyc", ".tsbuildinfo", ".db", ".zip", ".rar", ".7z", ".log"}
            and path.name not in {"package-integrity.json", "SOURCE_MANIFEST.md"})


PRIORITY = ["RUN_IN_CURSOR.md", "nawa.py", "nawa.code-workspace", ".vscode/", ".cursor/", "README.md", "docs/implementation/00_START_HERE.md", "docs/implementation/01_DOCUMENT_MAP.md", ".env.example", "pyproject.toml", "requirements.lock", "requirements-dev.lock", "backend/src/uae_ai/core/config.py", "backend/src/uae_ai/db.py", "alembic.ini", "migrations/", "backend/src/uae_ai/core/", "backend/src/uae_ai/domain/", "backend/src/uae_ai/seed.py", "backend/src/uae_ai/rag/", "backend/src/uae_ai/worker.py", "backend/src/uae_ai/graphs/", "backend/src/uae_ai/ml/", "backend/src/uae_ai/api/", "backend/src/uae_ai/main.py", "backend/src/uae_ai/cli.py", "apps/web/package", "apps/web/src/main.tsx", "apps/web/src/types.ts", "apps/web/src/api.ts", "apps/web/src/context.ts", "apps/web/src/i18n.tsx", "apps/web/src/ui.tsx", "apps/web/src/App.tsx", "apps/web/src/pages.tsx", "apps/web/src/workflows.tsx", "apps/web/src/styles.css", "apps/web/", "scripts/", "data/", "evals/", "tests/", "Dockerfile", "compose", "infra/", ".github/", "docs/implementation/", "docs/reference/", "docs/"]


def order(path):
    name = path.relative_to(ROOT).as_posix()
    score = next((i for i, prefix in enumerate(PRIORITY) if name == prefix or prefix.endswith("/") and name.startswith(prefix) or prefix.endswith("package") and name.startswith(prefix) or prefix == "compose" and name.startswith(prefix)), len(PRIORITY))
    return score, name


files = sorted((p for p in ROOT.rglob("*") if selected(p)), key=order)
index = ROOT / "docs/implementation/SOURCE_MANIFEST.md"
index.parent.mkdir(parents=True, exist_ok=True)
lines = ["# Delivered files in reading order", "", "Start at the top. Configuration, database and contracts precede services; shared frontend primitives precede screens. Runtime data, secrets, virtual environments and node_modules are intentionally excluded.", "", "| Order | File | Bytes |", "|---|---|---:|"]
entries = []
for i, path in enumerate(files, 1):
    name = path.relative_to(ROOT).as_posix()
    lines.append(f"| {i:03d} | `{name}` | {path.stat().st_size} |")
    entries.append({"order": i, "file": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
index.write_text("\n".join(lines)+"\n", encoding="utf-8")
integrity = ROOT / "docs/implementation/package-integrity.json"
integrity.write_text(json.dumps({"source_files": entries, "excludes": sorted(EXCLUDED), "notice": "Hashes cover source/content files before archive packaging; index/integrity files are included separately."}, indent=2), encoding="utf-8")
version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
archive = DEST / f"Nawa_Cursor_Ready_v{version}.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    for path in [index, integrity, *files]:
        z.write(path, "nawa-workspace/"+path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert all("/.data/" not in name and "/node_modules/" not in name and not name.endswith("/.env") for name in z.namelist())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(DEST/(archive.name+".sha256")).write_text(digest+"  "+archive.name+"\n")
print(f"Packaged {len(files)+2} files, {archive.stat().st_size:,} bytes: {archive}")

