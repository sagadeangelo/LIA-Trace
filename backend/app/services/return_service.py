
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryItem
from app.models.movement import InventoryMovement, MovementType
from app.models.returns import InventoryReturn, ReturnStatus
from app.services.inventory_service import MAX_QUANTITY


class ReturnServiceError(Exception):
    pass


def receive_return(
    db: Session,
    inventory_item_id: int,
    quantity: Decimal,
    reason: str,
    shipment_reference: str | None = None,
) -> InventoryReturn:
    """
    Recibe una devolucion sin aumentar el inventario.

    Las existencias solo aumentan cuando se aprueba
    la inspeccion correspondiente.
    """

    if not isinstance(quantity, Decimal):
        raise ReturnServiceError(
            "La cantidad debe ser decimal."
        )

    if not quantity.is_finite() or quantity <= 0:
        raise ReturnServiceError(
            "La cantidad debe ser positiva y finita."
        )

    if quantity > MAX_QUANTITY:
        raise ReturnServiceError(
            "La cantidad supera el limite permitido."
        )

    if quantity.as_tuple().exponent < -3:
        raise ReturnServiceError(
            "Solo se permiten tres decimales."
        )

    if not reason or not reason.strip():
        raise ReturnServiceError(
            "Debe indicar el motivo de la devolucion."
        )

    item = db.get(InventoryItem, inventory_item_id)

    if item is None:
        raise ReturnServiceError(
            "Articulo no encontrado."
        )

    inventory_return = InventoryReturn(
        inventory_item_id=inventory_item_id,
        quantity_received=quantity,
        quantity_approved=Decimal("0"),
        quantity_rejected=Decimal("0"),
        status=ReturnStatus.PENDING.value,
        reason=reason,
        original_shipment_reference=shipment_reference,
    )

    db.add(inventory_return)
    db.flush()

    return inventory_return


def inspect_return(
    db: Session,
    return_id: int,
    quantity_approved: Decimal,
    quantity_rejected: Decimal,
    inspection_notes: str,
) -> InventoryReturn:
    """
    Inspecciona una devolucion y reingresa lo aprobado.

    - Bloquea la devolucion durante la inspeccion.
    - Evita aprobar una devolucion dos veces.
    - Valida cantidades aprobadas y rechazadas.
    - Protege el limite numerico del inventario.
    - Registra un movimiento RETURN si hay aprobacion.

    El llamador debe ejecutar commit o rollback.
    """

    for quantity in (
        quantity_approved,
        quantity_rejected,
    ):
        if not isinstance(quantity, Decimal):
            raise ReturnServiceError(
                "Las cantidades deben ser decimales."
            )

        if not quantity.is_finite() or quantity < 0:
            raise ReturnServiceError(
                "Las cantidades deben ser finitas y no negativas."
            )

        if quantity > MAX_QUANTITY:
            raise ReturnServiceError(
                "La cantidad supera el limite permitido."
            )

        if quantity.as_tuple().exponent < -3:
            raise ReturnServiceError(
                "Solo se permiten tres decimales."
            )

    if not inspection_notes or not inspection_notes.strip():
        raise ReturnServiceError(
            "Debe registrar el resultado de la inspeccion."
        )

    statement = (
        select(InventoryReturn)
        .where(InventoryReturn.id == return_id)
        .with_for_update()
    )

    inventory_return = db.scalar(statement)

    if inventory_return is None:
        raise ReturnServiceError(
            "Devolucion no encontrada."
        )

    if inventory_return.status != ReturnStatus.PENDING.value:
        raise ReturnServiceError(
            "Esta devolucion ya fue inspeccionada."
        )

    total = quantity_approved + quantity_rejected

    if total != inventory_return.quantity_received:
        raise ReturnServiceError(
            "La suma aprobada y rechazada debe coincidir "
            "con la cantidad recibida."
        )

    item_statement = (
        select(InventoryItem)
        .where(
            InventoryItem.id == inventory_return.inventory_item_id
        )
        .with_for_update()
    )

    item = db.scalar(item_statement)

    if item is None:
        raise ReturnServiceError(
            "Articulo no encontrado."
        )

    # Proteger el inventario antes de modificar la devolucion.
    if quantity_approved > 0:
        new_quantity = item.quantity + quantity_approved

        if new_quantity > MAX_QUANTITY:
            raise ReturnServiceError(
                "El reingreso supera el limite del inventario."
            )

    # Registrar el resultado de la inspeccion.
    inventory_return.quantity_approved = quantity_approved
    inventory_return.quantity_rejected = quantity_rejected
    inventory_return.inspection_notes = inspection_notes
    inventory_return.inspected_at = datetime.now(timezone.utc)
    inventory_return.status = ReturnStatus.CLOSED.value

    # Solo lo aprobado aumenta las existencias.
    if quantity_approved > 0:
        item.quantity = new_quantity

        movement = InventoryMovement(
            inventory_item_id=item.id,
            movement_type=MovementType.RETURN.value,
            quantity=quantity_approved,
            reference=f"RETURN-{inventory_return.id}",
            notes=inspection_notes,
        )

        db.add(movement)

    db.flush()

    return inventory_return
