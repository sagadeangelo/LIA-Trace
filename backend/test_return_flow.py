
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.inventory import InventoryItem
from app.models.movement import InventoryMovement
from app.models.returns import InventoryReturn
from app.services.return_service import (
    ReturnServiceError,
    inspect_return,
    receive_return,
)


db = SessionLocal()

try:
    item = db.scalar(
        select(InventoryItem)
        .where(InventoryItem.id == 1)
        .with_for_update()
    )

    if item is None:
        raise RuntimeError("No existe el articulo de prueba ID 1.")

    initial_quantity = item.quantity

    print("INVENTARIO INICIAL:", initial_quantity)

    returned = receive_return(
        db=db,
        inventory_item_id=item.id,
        quantity=Decimal("5"),
        reason="Devolucion de prueba",
        shipment_reference="TEST-ENV-001",
    )

    assert item.quantity == initial_quantity
    assert returned.status == "PENDING"

    print("DEVOLUCION RECIBIDA:", returned.id)
    print("ESTADO:", returned.status)
    print("INVENTARIO SIN CAMBIOS:", item.quantity)

    inspected = inspect_return(
        db=db,
        return_id=returned.id,
        quantity_approved=Decimal("3"),
        quantity_rejected=Decimal("2"),
        inspection_notes="Tres piezas aprobadas y dos rechazadas",
    )

    assert inspected.status == "CLOSED"
    assert item.quantity == initial_quantity + Decimal("3")

    movement = db.scalar(
        select(InventoryMovement).where(
            InventoryMovement.reference == f"RETURN-{returned.id}"
        )
    )

    assert movement is not None
    assert movement.quantity == Decimal("3")

    print("APROBADAS:", inspected.quantity_approved)
    print("RECHAZADAS:", inspected.quantity_rejected)
    print("INVENTARIO DESPUES DE APROBACION:", item.quantity)
    print("MOVIMIENTO REGISTRADO:", movement.id)

    try:
        inspect_return(
            db=db,
            return_id=returned.id,
            quantity_approved=Decimal("3"),
            quantity_rejected=Decimal("2"),
            inspection_notes="Intento de segunda aprobacion",
        )
        raise AssertionError("ERROR: se permitio una doble aprobacion")

    except ReturnServiceError as error:
        print("DOBLE APROBACION BLOQUEADA:", error)

    db.rollback()

    print("ROLLBACK EJECUTADO")

    db.expire_all()

    persisted_item = db.get(InventoryItem, item.id)

    assert persisted_item.quantity == initial_quantity
    assert db.get(InventoryReturn, returned.id) is None

    print("INVENTARIO RESTAURADO:", persisted_item.quantity)
    print("PRUEBA COMPLETADA CORRECTAMENTE")

finally:
    db.rollback()
    db.close()
