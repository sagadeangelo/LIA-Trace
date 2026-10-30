
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.movement import InventoryMovement, MovementType
from app.schemas.movement import MovementCreate, MovementResponse
from app.services.inventory_service import (
    InventoryServiceError,
    register_movement,
)


router = APIRouter(
    prefix="/movements",
    tags=["Movements"],
)


def find_existing_movement(
    db: Session,
    idempotency_key: str,
) -> InventoryMovement | None:
    return db.scalar(
        select(InventoryMovement).where(
            InventoryMovement.idempotency_key == idempotency_key
        )
    )


def verify_same_request(
    existing: InventoryMovement,
    payload: MovementCreate,
) -> None:
    if (
        existing.inventory_item_id != payload.inventory_item_id
        or existing.movement_type != payload.movement_type
        or existing.quantity != payload.quantity
        or existing.reference != payload.reference
        or existing.notes != payload.notes
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "La clave de idempotencia ya fue utilizada "
                "con datos diferentes."
            ),
        )


@router.get("", response_model=list[MovementResponse])
def list_movements(
    inventory_item_id: int | None = None,
    db: Session = Depends(get_db),
):
    statement = select(InventoryMovement).order_by(
        InventoryMovement.id
    )

    if inventory_item_id is not None:
        statement = statement.where(
            InventoryMovement.inventory_item_id
            == inventory_item_id
        )

    return db.scalars(statement).all()


@router.get("/{movement_id}", response_model=MovementResponse)
def get_movement(
    movement_id: int,
    db: Session = Depends(get_db),
):
    movement = db.get(InventoryMovement, movement_id)

    if movement is None:
        raise HTTPException(
            status_code=404,
            detail="Movimiento no encontrado.",
        )

    return movement


@router.post("", response_model=MovementResponse, status_code=201)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
):
    try:
        movement_type = MovementType(payload.movement_type)

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Tipo de movimiento invalido.",
        )

    try:
        movement = register_movement(
            db=db,
            inventory_item_id=payload.inventory_item_id,
            movement_type=movement_type,
            quantity=payload.quantity,
            reference=payload.reference,
            notes=payload.notes,
            idempotency_key=payload.idempotency_key,
        )

        db.commit()
        db.refresh(movement)

        return movement

    except InventoryServiceError as error:
        db.rollback()

        message = str(error)

        status_code = (
            409
            if "clave de idempotencia ya fue utilizada" in message
            else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    except IntegrityError:
        db.rollback()

        # Una solicitud concurrente pudo registrar la misma clave.
        if payload.idempotency_key is not None:
            existing = find_existing_movement(
                db,
                payload.idempotency_key,
            )

            if existing is not None:
                verify_same_request(existing, payload)
                return existing

        raise HTTPException(
            status_code=409,
            detail="Conflicto al registrar el movimiento.",
        )
