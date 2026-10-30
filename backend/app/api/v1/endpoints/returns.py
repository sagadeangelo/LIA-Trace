
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.returns import InventoryReturn
from app.schemas.returns import (
    ReturnCreate,
    ReturnInspection,
    ReturnResponse,
)
from app.services.return_service import (
    ReturnServiceError,
    inspect_return,
    receive_return,
)


router = APIRouter(
    prefix="/returns",
    tags=["Returns"],
)


@router.post(
    "",
    response_model=ReturnResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_return(
    data: ReturnCreate,
    db: Session = Depends(get_db),
):
    try:
        inventory_return = receive_return(
            db=db,
            inventory_item_id=data.inventory_item_id,
            quantity=data.quantity,
            reason=data.reason,
            shipment_reference=data.shipment_reference,
        )

        db.commit()
        db.refresh(inventory_return)

        return inventory_return

    except ReturnServiceError as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get(
    "",
    response_model=list[ReturnResponse],
)
def list_returns(
    db: Session = Depends(get_db),
):
    statement = select(InventoryReturn).order_by(
        InventoryReturn.id
    )

    return db.scalars(statement).all()


@router.get(
    "/{return_id}",
    response_model=ReturnResponse,
)
def get_return(
    return_id: int,
    db: Session = Depends(get_db),
):
    inventory_return = db.get(InventoryReturn, return_id)

    if inventory_return is None:
        raise HTTPException(
            status_code=404,
            detail="Devolucion no encontrada.",
        )

    return inventory_return


@router.post(
    "/{return_id}/inspect",
    response_model=ReturnResponse,
)
def inspect_inventory_return(
    return_id: int,
    data: ReturnInspection,
    db: Session = Depends(get_db),
):
    try:
        inventory_return = inspect_return(
            db=db,
            return_id=return_id,
            quantity_approved=data.quantity_approved,
            quantity_rejected=data.quantity_rejected,
            inspection_notes=data.inspection_notes,
        )

        db.commit()
        db.refresh(inventory_return)

        return inventory_return

    except ReturnServiceError as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
