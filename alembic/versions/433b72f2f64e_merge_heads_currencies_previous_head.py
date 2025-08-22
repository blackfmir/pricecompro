"""merge heads (currencies + previous head)

Revision ID: 433b72f2f64e
Revises: 503e5942bf79, 760efb929bb6
Create Date: 2025-08-22 13:54:42.288680

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '433b72f2f64e'
down_revision: str | None = ('503e5942bf79', '760efb929bb6')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
