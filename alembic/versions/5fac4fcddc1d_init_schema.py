"""init schema

Revision ID: 5fac4fcddc1d
Revises: 65d411024827
Create Date: 2025-08-21 12:53:03.356355

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5fac4fcddc1d'
down_revision: str | None = '65d411024827'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
