from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect
from alembic.script import ScriptDirectory
import sqlite3
from uuid import uuid4
from uae_ai.db import Base


def config_for(url):
    root = Path(__file__).resolve().parents[4]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.attributes["database_url"] = url
    return config


def migrate_local(engine, url):
    tables = inspect(engine).get_table_names()
    if "cases" in tables and "alembic_version" not in tables:
        raise RuntimeError("An unversioned local schema exists. Verify and adopt it with: python -m uae_ai.cli adopt-local-schema")
    config=config_for(url)
    if engine.dialect.name=='sqlite' and 'alembic_version' in tables:
        with engine.connect() as connection:
            current=MigrationContext.configure(connection).get_current_revision()
        if current != ScriptDirectory.from_config(config).get_current_head() and engine.url.database not in {None,':memory:'}:
            file=Path(engine.url.database).resolve()
            backups=file.parent/'backups'
            backups.mkdir(mode=0o700,exist_ok=True)
            destination=backups/f'pre-migration-{uuid4().hex}.db'
            destination.touch(mode=0o600,exist_ok=False)
            with sqlite3.connect(file) as source,sqlite3.connect(destination) as target:
                source.backup(target)
            print('Created a consistent pre-migration SQLite backup in the database backups folder.')
    command.upgrade(config, "head")


def adopt_local(engine, url):
    with engine.connect() as connection:
        changes = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    if changes:
        raise RuntimeError("The existing schema differs from the baseline. Manual migration review required; no data was modified.")
    command.stamp(config_for(url), "head")

