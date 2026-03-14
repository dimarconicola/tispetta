from pathlib import Path

from sqlalchemy import inspect, text

from app.db.session import engine
from app.models import Base


def _table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    inspector = inspect(engine)
    return any(column['name'] == column_name for column in inspector.get_columns(table_name))


def _add_missing_column(table_name: str, column_name: str, column_sql: str) -> None:
    if _column_exists(table_name, column_name):
        return
    with engine.begin() as connection:
        connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}'))


def _ensure_normalized_document_columns() -> None:
    if not _table_exists('normalized_documents'):
        return
    _add_missing_column('normalized_documents', 'canonical_url', 'TEXT')
    _add_missing_column('normalized_documents', 'document_role', "VARCHAR(64) DEFAULT 'irrelevant'")
    _add_missing_column('normalized_documents', 'lifecycle_status', "VARCHAR(64) DEFAULT 'historical_reference'")
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE normalized_documents SET document_role = 'irrelevant' WHERE document_role IS NULL")
        )
        connection.execute(
            text(
                "UPDATE normalized_documents SET lifecycle_status = 'historical_reference' "
                "WHERE lifecycle_status IS NULL"
            )
        )


def _ensure_magic_link_columns() -> None:
    if not _table_exists('magic_link_tokens'):
        return
    _add_missing_column('magic_link_tokens', 'redirect_to', 'VARCHAR(255)')


def upgrade_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_normalized_document_columns()
    _ensure_magic_link_columns()


def init_db() -> None:
    upgrade_db()


def reset_db() -> None:
    if engine.url.get_backend_name() == 'sqlite' and engine.url.database and engine.url.database != ':memory:':
        engine.dispose()
        Path(engine.url.database).unlink(missing_ok=True)
        upgrade_db()
        return
    upgrade_db()
