"""add currencies and default_currency_id to price_lists

Revision ID: 61622b0fcb63
Revises: f67d5b309556
Create Date: 2025-08-22 02:15:25.126058

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '61622b0fcb63'
down_revision: str | None = 'f67d5b309556'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
