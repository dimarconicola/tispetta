from __future__ import annotations

from pathlib import Path

from app.db.migrations import run_migrations
from app.db.session import engine, normalized_database_url


def upgrade_db() -> None:
    run_migrations('head', normalized_database_url)


def init_db() -> None:
    upgrade_db()


def reset_db() -> None:
    if engine.url.get_backend_name() == 'sqlite' and engine.url.database and engine.url.database != ':memory:':
        engine.dispose()
        Path(engine.url.database).unlink(missing_ok=True)
    upgrade_db()
