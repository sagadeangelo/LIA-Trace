
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryItem
from app.models.movement import InventoryMovement, MovementType


class InventoryServiceError(Exception):
    pass


MAX_QUANTITY = Decimal("99999999999.999")


def register_movement(
    db: Session,
    inventory_item_id: int,
    movement_type: MovementType,
    quantity: Decimal,
    reference: str | None = None,
    notes: str | None = None,
    idempotency_key: str | None = None,
) -> InventoryMovement:

    # Validar tipo de movimiento
    if not isinstance(movement_type, MovementType):
        raise InventoryServiceError(
            "Tipo de movimiento invalido."
        )

    # Validar cantidad
    if not isinstance(quantity, Decimal):
        raise InventoryServiceError(
            "La cantidad debe ser decimal."
        )

    if not quantity.is_finite() or quantity <= 0:
        raise InventoryServiceError(
            "La cantidad debe ser positiva y finita."
        )

    if quantity > MAX_QUANTITY:
        raise InventoryServiceError(
            "La cantidad supera el limite permitido."
        )

    if quantity.as_tuple().exponent < -3:
        raise InventoryServiceError(
            "Solo se permiten tres decimales."
        )

    # Las devoluciones requieren inspeccion previa
    if movement_type == MovementType.RETURN:
        raise InventoryServiceError(
            "Las devoluciones requieren inspeccion previa."
        )

    # Validar clave de idempotencia
    if idempotency_key is not None:
        if not isinstance(idempotency_key, str):
            raise InventoryServiceError(
                "La clave de idempotencia debe ser texto."
            )

        if not idempotency_key.strip():
            raise InventoryServiceError(
                "La clave de idempotencia no puede estar vacia."
            )

        if len(idempotency_key) > 100:
            raise InventoryServiceError(
                "La clave de idempotencia supera 100 caracteres."
            )

    # Bloquear el articulo para evitar movimientos simultaneos
    item = db.scalar(
        select(InventoryItem)
        .where(InventoryItem.id == inventory_item_id)
        .with_for_update()
    )

    if item is None:
        raise InventoryServiceError(
            "Articulo no encontrado."
        )

    # Buscar un movimiento previo con la misma clave
    if idempotency_key is not None:
        existing = db.scalar(
            select(InventoryMovement).where(
                InventoryMovement.idempotency_key
                == idempotency_key
            )
        )

        if existing is not None:
            if (
                existing.inventory_item_id != inventory_item_id
                or existing.movement_type != movement_type.value
                or existing.quantity != quantity
                or existing.reference != reference
                or existing.notes != notes
            ):
                raise InventoryServiceError(
                    "La clave de idempotencia ya fue utilizada "
                    "con datos diferentes."
                )

            # Devolver el movimiento existente sin cambiar stock
            return existing

    # Calcular nuevas existencias
    try:
        if movement_type in (
            MovementType.ENTRY,
            MovementType.ADJUSTMENT_IN,
        ):
            new_quantity = item.quantity + quantity

        elif movement_type in (
            MovementType.EXIT,
            MovementType.ADJUSTMENT_OUT,
        ):
            new_quantity = item.quantity - quantity

            if new_quantity < 0:
                raise InventoryServiceError(
                    "Existencias insuficientes."
                )

        else:
            raise InventoryServiceError(
                "Movimiento no permitido."
            )

    except InvalidOperation as error:
        raise InventoryServiceError(
            "Error al calcular existencias."
        ) from error

    if new_quantity > MAX_QUANTITY:
        raise InventoryServiceError(
            "El inventario supera el limite permitido."
        )

    # Crear movimiento y actualizar existencias
    movement = InventoryMovement(
        inventory_item_id=inventory_item_id,
        movement_type=movement_type.value,
        quantity=quantity,
        reference=reference,
        notes=notes,
        idempotency_key=idempotency_key,
    )

    item.quantity = new_quantity
    db.add(movement)
    db.flush()

    return movement
