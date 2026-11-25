"""Verified offline SQLite + original-file bundles. Never includes .env or keys."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import zipfile
from sqlalchemy.engine import make_url


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def backup(database_url, data_dir, destination):
    destination, data_dir = Path(destination).resolve(), Path(data_dir).resolve()
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in {None, "", ":memory:"}:
        raise ValueError("This command supports file SQLite only. Use native PostgreSQL tools and an object-storage backup.")
    if destination.exists() or destination == data_dir or data_dir in destination.parents:
        raise ValueError("Choose a new backup file outside the active data directory")
    source = Path(url.database).resolve()
    if not source.is_file():
        raise ValueError("Source database does not exist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="nawa-backup-", dir=destination.parent) as temporary:
        temporary = Path(temporary)
        database = temporary / "database.sqlite3"
        # sqlite3.Connection's own context manager handles transactions, not
        # connection lifetime. Close handles before archiving/Windows cleanup.
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as current, closing(sqlite3.connect(database)) as copied:
            current.backup(copied)
            if copied.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Database integrity validation failed")
        files = {"database.sqlite3": database}
        uploads = data_dir / "uploads"
        if uploads.exists():
            if uploads.is_symlink():
                raise ValueError("Symlinked upload directories require an operator-managed backup")
            for file in uploads.iterdir():
                if not file.is_file() or file.is_symlink():
                    raise ValueError("Unexpected upload entry; inspect it before backup")
                files["uploads/" + file.name] = file
        manifest = {"format": "nawa-offline-backup-v1", "files": {name: {"sha256": digest(file), "bytes": file.stat().st_size} for name, file in files.items()}}
        packed = temporary / "backup.zip"
        with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, file in files.items():
                archive.write(file, name)
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        packed.chmod(0o600)
        # Exclusive destination creation prevents replacing an existing backup.
        with destination.open("xb") as output, packed.open("rb") as input_file:
            os.chmod(destination, 0o600)
            shutil.copyfileobj(input_file, output)
    return {"files": len(files), "sha256": digest(destination)}


def restore(archive_path, destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("Restore requires a new destination; existing data is never overwritten")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [entry.filename for entry in infos]
        if len(set(names)) != len(names) or len(names) > 10000 or sum(i.file_size for i in infos) > 1_000_000_000:
            raise ValueError("Invalid or excessive backup entries")
        for entry in infos:
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename or entry.is_dir() or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe backup entry")
            if entry.file_size > 256_000_000 or not (entry.filename in {"manifest.json", "database.sqlite3"} or len(path.parts) == 2 and path.parts[0] == "uploads"):
                raise ValueError("Unexpected backup content")
        if "manifest.json" not in names or archive.getinfo("manifest.json").file_size > 2_000_000:
            raise ValueError("Missing or excessive manifest")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("format") != "nawa-offline-backup-v1" or set(manifest["files"]) != set(names) - {"manifest.json"} or "database.sqlite3" not in manifest["files"]:
            raise ValueError("Backup manifest mismatch")
        with TemporaryDirectory(prefix="nawa-restore-", dir=destination.parent) as temporary:
            target = Path(temporary) / "restored"
            target.mkdir(mode=0o700)
            for name, expected in manifest["files"].items():
                file = target / name
                file.parent.mkdir(exist_ok=True, mode=0o700)
                with archive.open(name) as incoming, file.open("xb") as output:
                    shutil.copyfileobj(incoming, output)
                file.chmod(0o600)
                if digest(file) != expected["sha256"] or file.stat().st_size != expected["bytes"]:
                    raise ValueError("Backup checksum mismatch")
            # Windows must release the database file before publishing the folder.
            with closing(sqlite3.connect(target / "database.sqlite3")) as database:
                if database.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Restored database is invalid")
                database.execute("SELECT version_num FROM alembic_version").fetchone()
                database.execute("SELECT id FROM documents LIMIT 1").fetchall()
            (target / "uploads").mkdir(exist_ok=True, mode=0o700)
            if destination.exists():
                raise ValueError("Restore destination appeared during validation")
            target.rename(destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    save = commands.add_parser("backup")
    save.add_argument("destination")
    load = commands.add_parser("restore")
    load.add_argument("archive")
    load.add_argument("destination")
    args = parser.parse_args()
    if args.command == "backup":
        print(backup(os.environ.get("DATABASE_URL", "sqlite:///.data/nawa.db"), os.environ.get("DATA_DIR", ".data"), args.destination))
    else:
        print("Verified restore created:", restore(args.archive, args.destination))
