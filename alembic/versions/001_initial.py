"""Initial career schema.

Revision ID: 001_initial
Revises:
Create Date: 2026-09-27
"""

from __future__ import annotations

from alembic import op

from database.models import Base

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
