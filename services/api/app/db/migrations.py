from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine
from alembic.runtime.migration import MigrationContext

from app.core.config import get_settings

API_ROOT = Path(__file__).resolve().parents[2]


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    if database_url.startswith('postgresql://') and '+psycopg' not in database_url:
        return database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return database_url


def alembic_config(database_url: str | None = None) -> Config:
    settings = get_settings()
    config = Config(str(API_ROOT / 'alembic.ini'))
    config.set_main_option('script_location', str(API_ROOT / 'alembic'))
    config.set_main_option('sqlalchemy.url', normalize_database_url(database_url or settings.database_url))
    return config


def migration_engine(database_url: str | None = None) -> Engine:
    url = make_url(normalize_database_url(database_url or get_settings().database_url))
    connect_args = {'check_same_thread': False} if url.get_backend_name() == 'sqlite' else {}
    return create_engine(url, future=True, poolclass=NullPool, connect_args=connect_args)


def run_migrations(revision: str = 'head', database_url: str | None = None) -> None:
    command.upgrade(alembic_config(database_url), revision)


def stamp_revision(revision: str = 'head', database_url: str | None = None) -> None:
    command.stamp(alembic_config(database_url), revision)


def existing_tables(database_url: str | None = None) -> set[str]:
    engine = migration_engine(database_url)
    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


def current_revision(database_url: str | None = None) -> str | None:
    engine = migration_engine(database_url)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            if 'alembic_version' not in inspector.get_table_names():
                return None
            context = MigrationContext.configure(connection)
            return context.get_current_revision()
    finally:
        engine.dispose()


def head_revision(database_url: str | None = None) -> str:
    script = ScriptDirectory.from_config(alembic_config(database_url))
    return script.get_current_head()


def ensure_schema_revision(database_url: str | None = None) -> str:
    current = current_revision(database_url)
    if current:
        run_migrations('head', database_url)
        return current_revision(database_url) or head_revision(database_url)

    tables = existing_tables(database_url)
    materialized_tables = {table for table in tables if table != 'alembic_version'}
    if materialized_tables:
        stamp_revision('head', database_url)
        return head_revision(database_url)

    run_migrations('head', database_url)
    return current_revision(database_url) or head_revision(database_url)
