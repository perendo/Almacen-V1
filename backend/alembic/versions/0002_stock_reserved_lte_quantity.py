"""Añade la restricción de coherencia entre cantidad y reserva.

Revision ID: 0002_stock_reserved_lte_quantity
Revises: 0001_initial_schema
Create Date: 2026-11-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_stock_reserved_lte_quantity"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT_NAME = "ck_stock_reserved_lte_quantity"


def upgrade() -> None:
    op.create_check_constraint(
        CONSTRAINT_NAME,
        "stock",
        "reserved_quantity <= quantity",
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "stock", type_="check")
