"""Explicitly enabled synthetic-only runtime integration; no migration is run."""
from pathlib import Path

from .intake_scoped import ScopedIntake
from .intake_store import LocalIntakeStore
from .intake_migrate import verify_intake_migrations


def build_synthetic_intake(connect, directory, *, origin_policy='legacy_compatible'):
    if not directory or not Path(directory).is_absolute():
        raise ValueError('Synthetic intake requires an absolute storage directory')
    with connect() as conn:
        verify_intake_migrations(conn)
    return ScopedIntake(connect, LocalIntakeStore(directory), origin_policy=origin_policy)
