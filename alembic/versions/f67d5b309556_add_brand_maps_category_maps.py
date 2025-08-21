"""add brand_maps & category_maps

Revision ID: f67d5b309556
Revises: 5fac4fcddc1d
Create Date: 2025-08-21 20:24:51.177095

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f67d5b309556'
down_revision: str | None = '5fac4fcddc1d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
