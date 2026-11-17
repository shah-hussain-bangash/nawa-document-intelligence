"""Explicitly enabled synthetic-only runtime integration; no migration is run."""
from pathlib import Path

from .intake_scoped import ScopedIntake
from .intake_store import LocalIntakeStore


def build_synthetic_intake(connect, directory):
    if not directory or not Path(directory).is_absolute():
        raise ValueError('Synthetic intake requires an absolute storage directory')
    with connect() as conn:
        row = conn.execute("SELECT to_regclass('nawa_intake_documents'), to_regclass('nawa_intake_jobs')").fetchone()
        if not row or any(value is None for value in row):
            raise ValueError('Synthetic intake schema is not installed')
    return ScopedIntake(connect, LocalIntakeStore(directory))
