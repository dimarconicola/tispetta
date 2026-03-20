from pathlib import Path

from sqlalchemy import create_engine

from app.db.migrations import current_revision, ensure_schema_revision, existing_tables, head_revision
from app.models import Base


def test_ensure_schema_revision_bootstraps_empty_sqlite_db(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'empty.db'}"

    revision = ensure_schema_revision(database_url)

    assert revision == head_revision(database_url)
    assert current_revision(database_url) == head_revision(database_url)
    assert 'users' in existing_tables(database_url)
    assert 'alembic_version' in existing_tables(database_url)


def test_ensure_schema_revision_stamps_legacy_schema_without_running_baseline(tmp_path: Path) -> None:
    db_path = tmp_path / 'legacy.db'
    database_url = f'sqlite:///{db_path}'

    legacy_engine = create_engine(database_url, future=True)
    try:
        Base.metadata.create_all(legacy_engine)
    finally:
        legacy_engine.dispose()

    assert current_revision(database_url) is None
    assert 'users' in existing_tables(database_url)
    assert 'alembic_version' not in existing_tables(database_url)

    revision = ensure_schema_revision(database_url)

    assert revision == head_revision(database_url)
    assert current_revision(database_url) == head_revision(database_url)
    assert 'users' in existing_tables(database_url)
    assert 'alembic_version' in existing_tables(database_url)
