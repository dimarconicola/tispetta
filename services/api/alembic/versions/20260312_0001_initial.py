"""Initial schema baseline.

Revision ID: 20260312_0001
Revises:
Create Date: 2026-03-12
"""

from collections.abc import Sequence

from alembic import op

from app.models import Base


revision: str = '20260312_0001'
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
