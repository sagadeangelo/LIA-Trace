
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MovementCreate(BaseModel):
    inventory_item_id: int = Field(gt=0)

    movement_type: str = Field(
        min_length=1,
        max_length=30,
    )

    quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
        allow_inf_nan=False,
    )

    reference: str | None = Field(
        default=None,
        max_length=150,
    )

    notes: str | None = None

    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_item_id: int
    movement_type: str
    quantity: Decimal
    reference: str | None
    notes: str | None
    idempotency_key: str | None
    created_at: datetime
