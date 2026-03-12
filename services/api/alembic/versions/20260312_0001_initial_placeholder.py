"""Initial placeholder migration.

Revision ID: 20260312_0001
Revises:
Create Date: 2026-03-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '20260312_0001'
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Schema bootstrap is currently handled by SQLAlchemy metadata create_all during local development.
    # Keep this placeholder so Alembic is wired and ready for incremental revisions.
    pass



def downgrade() -> None:
    pass
