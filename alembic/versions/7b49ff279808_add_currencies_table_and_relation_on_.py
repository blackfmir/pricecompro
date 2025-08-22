"""add currencies table and relation on price_lists

Revision ID: 7b49ff279808
Revises: 61622b0fcb63
Create Date: 2025-08-22 04:24:25.768654

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7b49ff279808'
down_revision: str | None = '61622b0fcb63'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
