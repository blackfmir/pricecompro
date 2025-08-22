import contextlib
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dc30f9986037"
down_revision: str | None = "7b49ff279808"  # лиши як у тебе
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    # 1) Створити currencies, якщо її ще нема
    if "currencies" not in tables:
        op.create_table(
            "currencies",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("iso_code", sa.String(length=8), nullable=False),
            sa.Column("symbol_left", sa.String(length=8), nullable=True),
            sa.Column("symbol_right", sa.String(length=8), nullable=True),
            sa.Column("decimals", sa.Integer(), nullable=False, server_default=sa.text("2")),
            sa.Column("rate", sa.Float(), nullable=False, server_default=sa.text("1.0")),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.UniqueConstraint("iso_code", name="uq_currencies_iso_code"),
        )

    # 2) Додати колонку у price_lists, якщо її ще нема
    if "price_lists" in tables:
        cols = [c["name"] for c in insp.get_columns("price_lists")]
        if "default_currency_id" not in cols:
            # Для SQLite — через batch_alter_table (перебудова таблиці)
            with op.batch_alter_table("price_lists") as batch:
                batch.add_column(sa.Column("default_currency_id", sa.Integer(), nullable=True))
                # створення FK — м'яко пробуємо
                with contextlib.suppress(Exception):
                    batch.create_foreign_key(
                        "fk_price_lists_default_currency_id_currencies",
                        "currencies",
                        ["default_currency_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if "price_lists" in tables:
        cols = [c["name"] for c in insp.get_columns("price_lists")]
        if "default_currency_id" in cols:
            with op.batch_alter_table("price_lists") as batch:
                with contextlib.suppress(Exception):
                    batch.drop_constraint(
                        "fk_price_lists_default_currency_id_currencies",
                        type_="foreignkey",
                    )
                batch.drop_column("default_currency_id")

    if "currencies" in tables:
        op.drop_table("currencies")
