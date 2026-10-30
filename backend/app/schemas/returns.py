
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReturnCreate(BaseModel):
    inventory_item_id: int = Field(gt=0)

    quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
        allow_inf_nan=False,
    )

    reason: str = Field(min_length=1)

    shipment_reference: str | None = Field(
        default=None,
        max_length=150,
    )


class ReturnInspection(BaseModel):
    quantity_approved: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=3,
        allow_inf_nan=False,
    )

    quantity_rejected: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=3,
        allow_inf_nan=False,
    )

    inspection_notes: str = Field(min_length=1)


class ReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_item_id: int

    quantity_received: Decimal
    quantity_approved: Decimal
    quantity_rejected: Decimal

    status: str
    reason: str
    original_shipment_reference: str | None
    inspection_notes: str | None

    received_at: datetime
    inspected_at: datetime | None
