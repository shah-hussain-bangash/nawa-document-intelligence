from pathlib import Path

import pytest

from scripts.validate_windows_lock import entries, project

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("filename", ["requirements.lock", "requirements-dev.lock"])
@pytest.mark.parametrize("python", ["3.12", "3.13"])
def test_windows_psycopg_timezone_dependency_is_locked(filename, python):
    windows = project(ROOT / filename, python)
    assert "psycopg" in windows
    assert "tzdata" in windows, "psycopg requires tzdata on Windows; hash mode must not discover it unpinned"
    assert windows["tzdata"][2]


@pytest.mark.parametrize("python", ["3.12", "3.13"])
def test_windows_pytest_console_dependency_is_locked(python):
    windows = project(ROOT / "requirements-dev.lock", python)
    assert "pytest" in windows
    assert "colorama" in windows, "pytest requires colorama on Windows"
    assert windows["colorama"][2]


@pytest.mark.parametrize("filename", ["requirements.lock", "requirements-dev.lock"])
def test_every_universal_lock_entry_is_pinned_and_hashed(filename):
    assert len(entries(ROOT / filename)) > 30
