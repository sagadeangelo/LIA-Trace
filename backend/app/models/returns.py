
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReturnStatus(str, Enum):
    PENDING = "PENDING"
    INSPECTED = "INSPECTED"
    CLOSED = "CLOSED"


class InventoryReturn(Base):
    __tablename__ = "inventory_returns"

    __table_args__ = (
        CheckConstraint(
            "quantity_received > 0",
            name="ck_return_quantity_positive",
        ),
        CheckConstraint(
            "quantity_approved >= 0 AND quantity_rejected >= 0",
            name="ck_return_quantities_nonnegative",
        ),
        CheckConstraint(
            "quantity_approved + quantity_rejected <= quantity_received",
            name="ck_return_quantities_limit",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_items.id"),
        nullable=False,
        index=True,
    )

    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    quantity_approved: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=0,
    )

    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ReturnStatus.PENDING.value,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    original_shipment_reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    inspection_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    inspected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
