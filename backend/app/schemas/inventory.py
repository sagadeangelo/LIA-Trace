
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemCreate(BaseModel):
    """Datos necesarios para registrar un articulo."""

    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    unit: str = Field(
        default="pieza",
        min_length=1,
        max_length=30,
    )

    quantity: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=14,
        decimal_places=3,
    )


class InventoryItemResponse(InventoryItemCreate):
    """Datos devueltos por la API de inventario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
