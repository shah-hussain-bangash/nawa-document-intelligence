"""Portable dataset decoding, temporary DB cleanup and configured CLI dispatch."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from sqlalchemy import event

from scripts import devtools, evaluate_quality as quality
from uae_ai.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_quality_reads_bilingual_dataset_under_legacy_default_encoding():
    code = """
import json, locale, sys
from scripts.evaluate_quality import evaluate
from uae_ai.core.config import Settings
assert sys.flags.utf8_mode == 0
report = evaluate(Settings(app_env='test', auth_mode='demo', retrieval_mode='lexical', model_mode='extractive', ocr_mode='off'))
assert report['questions'] == 100
assert sum(row['language'] == 'ar' for row in report['results']) == 50
print(json.dumps({'questions':report['questions'], 'encoding':locale.getpreferredencoding(False)}))
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend/src"),
           "LC_ALL": "C", "LANG": "C", "PYTHONCOERCECLOCALE": "0",
           "PYTHONUTF8": "0", "PYTHONIOENCODING": "ascii"}
    result = subprocess.run([sys.executable, "-X", "utf8=0", "-c", code],
                            cwd=ROOT, env=env, capture_output=True, timeout=90)
    assert result.returncode == 0, result.stderr.decode("ascii", errors="backslashreplace")
    assert json.loads(result.stdout)["questions"] == 100


def test_quality_closes_database_before_cleanup_when_search_fails(monkeypatch):
    make_database = quality.make_database
    temporary_directory = quality.TemporaryDirectory
    connections = []
    cleanup_checked = []

    def tracked_database(url):
        engine, factory = make_database(url)
        event.listen(engine, "connect", lambda connection, _: connections.append(connection))
        return engine, factory

    @contextmanager
    def checked_directory(**kwargs):
        with temporary_directory(**kwargs) as directory:
            try:
                yield directory
            finally:
                for connection in connections:
                    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                        connection.execute("SELECT 1")
                cleanup_checked.append(True)

    def failed_search(*args):
        raise RuntimeError("synthetic search failure")

    monkeypatch.setattr(quality, "make_database", tracked_database)
    monkeypatch.setattr(quality, "TemporaryDirectory", checked_directory)
    monkeypatch.setattr(quality, "search", failed_search)
    with pytest.raises(RuntimeError, match="synthetic search failure"):
        quality.evaluate(Settings(app_env="test", auth_mode="demo", retrieval_mode="lexical", model_mode="extractive"))
    assert connections and cleanup_checked == [True]


def test_quality_command_loads_local_config_and_forwards_output(tmp_path, monkeypatch):
    for key in ["RETRIEVAL_MODE", "EMBEDDING_MODEL"]:
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text("RETRIEVAL_MODE=hybrid\nEMBEDDING_MODEL=embeddinggemma:300m\n", encoding="utf-8")
    monkeypatch.setattr(devtools, "ROOT", tmp_path)
    monkeypatch.setattr(devtools, "require_environment", lambda: Path(sys.executable))
    calls = []
    monkeypatch.setattr(devtools, "checked", lambda command, **kwargs: calls.append((command, kwargs)))
    devtools.main(["quality", "--output", "artifacts/quality-hybrid.json"])
    command, options = calls[0]
    assert command == [Path(sys.executable), "-m", "scripts.evaluate_quality", "--output", "artifacts/quality-hybrid.json"]
    assert options["env"]["RETRIEVAL_MODE"] == "hybrid"
    assert options["env"]["EMBEDDING_MODEL"] == "embeddinggemma:300m"
