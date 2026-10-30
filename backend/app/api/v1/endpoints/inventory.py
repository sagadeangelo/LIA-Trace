
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.inventory import InventoryItem
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemResponse,
)


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


@router.post(
    "",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_item(
    item: InventoryItemCreate,
    db: Session = Depends(get_db),
):
    """Registrar un nuevo articulo de inventario."""

    db_item = InventoryItem(**item.model_dump())

    db.add(db_item)

    try:
        db.commit()
        db.refresh(db_item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un articulo con ese SKU.",
        )

    return db_item


@router.get(
    "",
    response_model=list[InventoryItemResponse],
)
def list_inventory_items(
    db: Session = Depends(get_db),
):
    """Consultar los articulos registrados."""

    statement = select(InventoryItem).order_by(InventoryItem.id)

    return db.scalars(statement).all()


@router.get(
    "/{item_id}",
    response_model=InventoryItemResponse,
)
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Consultar un articulo por su identificador."""

    item = db.get(InventoryItem, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Articulo no encontrado.",
        )

    return item
