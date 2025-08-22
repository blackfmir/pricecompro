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


def upgrade() -> None:
    # 1) Заповнити NULL-и поточним часом, щоб можна було зробити NOT NULL
    op.execute(
        "UPDATE supplier_products "
        "SET updated_at = CURRENT_TIMESTAMP "
        "WHERE updated_at IS NULL"
    )

    # 2) Змінити колонку в batch-режимі (SQLite-friendly)
    with op.batch_alter_table("supplier_products", recreate="always") as batch:
        batch.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            existing_server_default=None,
        )


def downgrade() -> None:
    # Повернути nullable та прибрати server_default
    with op.batch_alter_table("supplier_products", recreate="always") as batch:
        batch.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=False),
            nullable=True,
            server_default=None,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

