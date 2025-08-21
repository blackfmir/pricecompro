"""supplier_products.updated_at: add server_default and non-null

Revision ID: a03ccacc0b69
Revises: 
Create Date: 2025-08-21 00:38:51.206905

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.sql import func

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a03ccacc0b69'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    # Для SQLite зміна default робиться через alter_column з server_default (SQLAlchemy сам перегенерує DDL)
    op.alter_column(
        "supplier_products",
        "updated_at",
        existing_type=sa.DateTime(),
        server_default=sa.text("(CURRENT_TIMESTAMP)"),
        existing_nullable=True,   # якщо було True
        nullable=False,
    )

def downgrade():
    op.alter_column(
        "supplier_products",
        "updated_at",
        existing_type=sa.DateTime(),
        server_default=None,
        nullable=True,
    )

