
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.movement import MovementType
from app.services.inventory_service import (
    InventoryServiceError,
    register_movement,
)

db = SessionLocal()

try:
    register_movement(
        db=db,
        inventory_item_id=1,
        movement_type=MovementType.RETURN,
        quantity=Decimal("1"),
    )

    print("ERROR: devolucion permitida")

except InventoryServiceError as error:
    print("DEVOLUCION BLOQUEADA:", error)

finally:
    db.rollback()
    db.close()
