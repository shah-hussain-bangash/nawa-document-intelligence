"""Require closed SQLite handles before Windows-sensitive cleanup/publication."""
from contextlib import closing, contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

import pytest

from scripts import backup_workspace as bundles


@pytest.fixture
def source(tmp_path):
    data = tmp_path / "active data"
    (data / "uploads").mkdir(parents=True)
    database = data / "nawa.db"
    with closing(sqlite3.connect(database)) as db:
        db.executescript("CREATE TABLE alembic_version (version_num TEXT);"
                         "INSERT INTO alembic_version VALUES ('7f0600000001');"
                         "CREATE TABLE documents (id TEXT);"
                         "INSERT INTO documents VALUES ('source-1');")
    (data / "uploads/source-1.txt").write_bytes(b"Original synthetic source")
    (data / ".env").write_bytes(b"PRIVATE_CONFIG=test-only")
    return database, data, tmp_path / "saved backup.zip"


@pytest.fixture
def windows_boundaries(monkeypatch):
    connect = sqlite3.connect
    temporary_directory = bundles.TemporaryDirectory
    rename = Path.rename
    connections, boundaries = [], []

    def tracked_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        # Retain references: garbage collection must not conceal leaked handles.
        connections.append(connection)
        return connection

    def require_closed():
        for connection in connections:
            with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                connection.execute("SELECT 1")

    @contextmanager
    def checked_temporary_directory(**kwargs):
        with temporary_directory(**kwargs) as name:
            try:
                yield name
            finally:
                require_closed()
                boundaries.append("temporary cleanup")

    def checked_rename(path, target):
        require_closed()
        boundaries.append("restore publication")
        return rename(path, target)

    monkeypatch.setattr(bundles.sqlite3, "connect", tracked_connect)
    monkeypatch.setattr(bundles, "TemporaryDirectory", checked_temporary_directory)
    monkeypatch.setattr(Path, "rename", checked_rename)
    return connections, boundaries


def test_backup_and_restore_close_handles_before_cleanup_and_publication(source, windows_boundaries):
    database, data, archive = source
    before = database.read_bytes()
    result = bundles.backup(f"sqlite:///{database.as_posix()}", data, archive)
    assert result["files"] == 2
    assert result["sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    restored = bundles.restore(archive, data.parent / "restored data")
    assert (restored / "uploads/source-1.txt").read_bytes() == b"Original synthetic source"
    assert not (restored / ".env").exists()
    assert database.read_bytes() == before
    connections, boundaries = windows_boundaries
    assert len(connections) == 3
    assert boundaries == ["temporary cleanup", "restore publication", "temporary cleanup"]
    assert not list(archive.parent.glob("nawa-backup-*"))
    assert not list(archive.parent.glob("nawa-restore-*"))


def test_corrupt_database_backup_releases_handles_and_preserves_source(source, windows_boundaries):
    database, data, archive = source
    database.write_bytes(b"invalid SQLite database")
    with pytest.raises(sqlite3.DatabaseError):
        bundles.backup(f"sqlite:///{database.as_posix()}", data, archive)
    assert database.read_bytes() == b"invalid SQLite database"
    assert not archive.exists()
    assert windows_boundaries[1] == ["temporary cleanup"]
    assert not list(archive.parent.glob("nawa-backup-*"))


def test_corrupt_database_restore_releases_handle_without_publishing(source, windows_boundaries):
    database, data, archive = source
    contents = b"invalid SQLite database"
    manifest = {"format": "nawa-offline-backup-v1", "files": {
        "database.sqlite3": {"sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents)}}}
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("database.sqlite3", contents)
        output.writestr("manifest.json", json.dumps(manifest))
    destination = data.parent / "restored data"
    with pytest.raises(sqlite3.DatabaseError):
        bundles.restore(archive, destination)
    assert not destination.exists()
    assert database.exists()
    assert windows_boundaries[1] == ["temporary cleanup"]
    assert not list(archive.parent.glob("nawa-restore-*"))


def test_backup_closes_source_when_opening_destination_fails(source, windows_boundaries, monkeypatch):
    database, data, archive = source
    connect = bundles.sqlite3.connect

    def fail_destination(path, *args, **kwargs):
        if Path(str(path)).name == "database.sqlite3":
            raise OSError("synthetic destination-open failure")
        return connect(path, *args, **kwargs)

    monkeypatch.setattr(bundles.sqlite3, "connect", fail_destination)
    with pytest.raises(OSError, match="destination-open failure"):
        bundles.backup(f"sqlite:///{database.as_posix()}", data, archive)
    assert not archive.exists()
    assert windows_boundaries[1] == ["temporary cleanup"]
