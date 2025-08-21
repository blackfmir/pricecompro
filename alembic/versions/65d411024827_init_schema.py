"""init schema

Revision ID: 65d411024827
Revises: a03ccacc0b69
Create Date: 2025-08-21 04:21:12.180796

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '65d411024827'
down_revision: str | None = 'a03ccacc0b69'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
