"""Project universal locks onto Windows and check downloaded wheel metadata.

This validates pin/hash coverage and transitive Windows requirements without
claiming native Windows execution. Run after installing development dependencies.
"""
import argparse
from collections import deque
from email.parser import BytesParser
from pathlib import Path
import re
import tomllib
import zipfile

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]


def entries(path):
    buffer = ""
    result = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        continuation = line.endswith("\\")
        buffer += " " + (line[:-1].strip() if continuation else line)
        if continuation:
            continue
        hashes = re.findall(r"--hash=sha256:[0-9a-f]{64}", buffer)
        requirement = Requirement(re.sub(r"\s+--hash=sha256:[0-9a-f]{64}", "", buffer).strip())
        pins = list(requirement.specifier)
        if len(pins) != 1 or pins[0].operator != "==" or "*" in pins[0].version or not hashes:
            raise ValueError(f"Unpinned or unhashed lock entry: {requirement.name}")
        result.append((requirement, pins[0].version, hashes))
        buffer = ""
    if buffer.strip():
        raise ValueError("Incomplete lock continuation")
    return result


def windows_environment(python="3.12"):
    env = default_environment()
    env.update(os_name="nt", sys_platform="win32", platform_system="Windows", platform_machine="AMD64", python_version=python, python_full_version=python+".0", implementation_version=python+".0", implementation_name="cpython", platform_python_implementation="CPython")
    return env


def project(path, python="3.12"):
    environment = windows_environment(python)
    selected = {}
    for requirement, version, hashes in entries(path):
        if requirement.marker and not requirement.marker.evaluate(environment):
            continue
        key = canonicalize_name(requirement.name)
        if key in selected and selected[key][1] != version:
            raise ValueError(f"Conflicting Windows versions for {key}")
        selected[key] = (requirement, version, hashes)
    return selected


def export(path, destination):
    selected = project(path)
    lines = ["# Windows CPython 3.12 projection of the universal hash lock."]
    for name, (_, version, hashes) in sorted(selected.items()):
        lines.append(f"{name}=={version} " + " ".join(hashes))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines)+"\n")
    print(f"Exported {len(selected)} pinned/hashed Windows requirements.")


def validate_metadata(lock, directory):
    selected = project(lock)
    metadata = {}
    for path in directory.glob("*.whl"):
        with zipfile.ZipFile(path) as archive:
            item = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
            data = BytesParser().parsebytes(archive.read(item))
        metadata[canonicalize_name(data["Name"])] = data
    missing = set(selected) - set(metadata)
    if missing:
        raise ValueError("Missing verified wheels: " + ", ".join(sorted(missing)))
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    roots = config["project"]["dependencies"] + config["project"]["optional-dependencies"]["test"]
    queue = deque(Requirement(text) for text in roots)
    seen = set()
    count = 0
    environment = windows_environment()
    while queue:
        requirement = queue.popleft()
        name = canonicalize_name(requirement.name)
        if name not in selected:
            raise ValueError(f"Unpinned Windows dependency: {requirement}")
        version = selected[name][1]
        if Version(version) not in requirement.specifier:
            raise ValueError(f"Version mismatch: {requirement}, selected {version}")
        key = (name, tuple(sorted(requirement.extras)))
        if key in seen:
            continue
        seen.add(key)
        for text in metadata[name].get_all("Requires-Dist", []):
            dependency = Requirement(text)
            if dependency.marker and not any(dependency.marker.evaluate({**environment, "extra": extra}) for extra in {"", *requirement.extras}):
                continue
            queue.append(dependency)
            count += 1
    print(f"PASS: {len(selected)} Windows wheels; {count} applicable dependency edges have pinned compatible versions, including extras.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["export", "validate"])
    parser.add_argument("--lock", type=Path, default=ROOT/"requirements-dev.lock")
    parser.add_argument("--output", type=Path, default=ROOT/"artifacts/windows-verified.requirements.txt")
    parser.add_argument("--wheels", type=Path, default=Path("/tmp/nawa-windows-wheels"))
    args = parser.parse_args()
    export(args.lock, args.output) if args.command == "export" else validate_metadata(args.lock, args.wheels)

