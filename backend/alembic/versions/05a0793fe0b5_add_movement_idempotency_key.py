
"""add movement idempotency key

Revision ID: 05a0793fe0b5
Revises: c21606a02817
Create Date: 2026-10-30 18:15:20.566076
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "05a0793fe0b5"
down_revision: Union[str, Sequence[str], None] = "c21606a02817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add an optional, unique idempotency key to movements."""

    op.add_column(
        "inventory_movements",
        sa.Column(
            "idempotency_key",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.create_unique_constraint(
        "uq_inventory_movements_idempotency_key",
        "inventory_movements",
        ["idempotency_key"],
    )


def downgrade() -> None:
    """Remove the idempotency key from movements."""

    op.drop_constraint(
        "uq_inventory_movements_idempotency_key",
        "inventory_movements",
        type_="unique",
    )

    op.drop_column(
        "inventory_movements",
        "idempotency_key",
    )
