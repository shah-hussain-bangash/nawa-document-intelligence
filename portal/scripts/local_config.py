"""Shared literal UTF-8 .env loading. Never prints configuration values."""
import os
from pathlib import Path
import re
import secrets


def read_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    result = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise ValueError(f"Invalid .env syntax on line {number}; expected NAME=value.")
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid .env setting name on line {number}.")
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unclosed .env quote for {name} on line {number}.")
            value = value[1:-1]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        result[name] = value
    return result


def local_environment(root: Path) -> dict[str, str]:
    # Explicit shell settings take precedence. Do not interpolate or execute .env.
    result = read_env(root / ".env")
    result.update(os.environ)
    source = str(root / "backend" / "src")
    result["PYTHONPATH"] = source + os.pathsep + result.get("PYTHONPATH", "")
    return result


def initialise_env(root: Path) -> str:
    path = root / ".env"
    if not path.exists():
        path.write_text((root / ".env.example").read_text(encoding="utf-8") + "\nPOSTGRES_PASSWORD=" + secrets.token_hex(24) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
        return "Created ignored local .env; no credential values printed."
    saved = read_env(path)
    # Supported additive correction; preserve every existing value and comment.
    if "POSTGRES_PASSWORD" not in saved and not os.environ.get("POSTGRES_PASSWORD"):
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\nPOSTGRES_PASSWORD=" + secrets.token_hex(24) + "\n")
        return "Preserved existing .env and added the missing local database password."
    return "Existing .env and bindings preserved."

