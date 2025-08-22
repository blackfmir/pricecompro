"""add currencies table + price_lists.default_currency_id

Revision ID: 6f22f0cd82fc
Revises: dc30f9986037
Create Date: 2025-08-22 12:10:06.709776

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6f22f0cd82fc'
down_revision: str | None = 'dc30f9986037'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
