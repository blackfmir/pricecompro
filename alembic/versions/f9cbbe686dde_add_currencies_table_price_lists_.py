"""add currencies table + price_lists.default_currency_id"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "760efb929bb6"
down_revision: str | None = "6f22f0cd82fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) Таблиця currencies
    op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("iso_code", sa.String(length=8), nullable=False, unique=True),
        sa.Column("symbol_left", sa.String(length=8), nullable=True),
        sa.Column("symbol_right", sa.String(length=8), nullable=True),
        sa.Column("decimals", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("rate", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )

    # 2) Колонка-foreign key у price_lists
    op.add_column(
        "price_lists",
        sa.Column("default_currency_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_price_lists_default_currency_id",
        "price_lists",
        ["default_currency_id"],
    )
    op.create_foreign_key(
        "fk_price_lists_default_currency",
        "price_lists",
        "currencies",
        ["default_currency_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 3) Seed: PLN як основна валюта
    currencies_tbl = sa.table(
        "currencies",
        sa.column("name", sa.String),
        sa.column("iso_code", sa.String),
        sa.column("symbol_left", sa.String),
        sa.column("symbol_right", sa.String),
        sa.column("decimals", sa.Integer),
        sa.column("rate", sa.Float),
        sa.column("is_primary", sa.Boolean),
        sa.column("active", sa.Boolean),
    )
    op.bulk_insert(
        currencies_tbl,
        [
            {
                "name": "Polski złoty",
                "iso_code": "PLN",
                "symbol_left": "",
                "symbol_right": "zł",
                "decimals": 2,
                "rate": 1.0,
                "is_primary": True,
                "active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_price_lists_default_currency", "price_lists", type_="foreignkey"
    )
    op.drop_index("ix_price_lists_default_currency_id", table_name="price_lists")
    op.drop_column("price_lists", "default_currency_id")
    op.drop_table("currencies")
