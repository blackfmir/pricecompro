from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "503e5942bf79"
down_revision: str | None = "a03ccacc0b69"  # залиш якщо так і є
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) Створюємо таблицю валют
    op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("iso_code", sa.String(length=8), nullable=False, unique=True),
        sa.Column("symbol_left", sa.String(length=8), nullable=True),
        sa.Column("symbol_right", sa.String(length=8), nullable=True),
        sa.Column("decimals", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column("rate", sa.Numeric(18, 6), nullable=False, server_default=sa.text("1.0")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # 2) Додаємо колонку у price_lists + FK
    op.add_column("price_lists", sa.Column("default_currency_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_price_lists_default_currency_id_currencies",
        source_table="price_lists",
        referent_table="currencies",
        local_cols=["default_currency_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_price_lists_default_currency_id_currencies", "price_lists", type_="foreignkey")
    op.drop_column("price_lists", "default_currency_id")
    op.drop_table("currencies")
