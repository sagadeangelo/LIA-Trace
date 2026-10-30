
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

URL = "http://localhost:8000/api/v1/movements"

IDEMPOTENCY_KEY = "LIA-IDEMP-CONCURRENTE-001"

payload = {
    "inventory_item_id": 1,
    "movement_type": "ENTRY",
    "quantity": 1,
    "reference": "PRUEBA-CONCURRENCIA-001",
    "idempotency_key": IDEMPOTENCY_KEY,
}

# Coordina el inicio de las dos solicitudes.
barrier = Barrier(2)


def enviar_solicitud(numero):
    datos = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        URL,
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    barrier.wait(timeout=10)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            contenido = json.loads(
                response.read().decode("utf-8")
            )

            return {
                "solicitud": numero,
                "http": response.status,
                "id": contenido.get("id"),
                "clave": contenido.get("idempotency_key"),
            }

    except urllib.error.HTTPError as error:
        return {
            "solicitud": numero,
            "http": error.code,
            "error": error.read().decode("utf-8"),
        }

    except Exception as error:
        return {
            "solicitud": numero,
            "error": str(error),
        }


def main():
    print("PRUEBA DE IDEMPOTENCIA CONCURRENTE")
    print("Clave:", IDEMPOTENCY_KEY)
    print("--------------------------------")

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(
            executor.map(enviar_solicitud, [1, 2])
        )

    for resultado in resultados:
        print(resultado)

    exitosos = [
        r for r in resultados
        if r.get("http") in (200, 201)
    ]

    ids = {
        r.get("id")
        for r in exitosos
        if r.get("id") is not None
    }

    print("--------------------------------")
    print("Respuestas exitosas:", len(exitosos))
    print("IDs diferentes:", len(ids))

    if len(exitosos) == 2 and len(ids) == 1:
        print("RESULTADO: Ambas solicitudes devolvieron el mismo movimiento.")
    else:
        print("RESULTADO: Requiere revision de las respuestas.")

    print("IMPORTANTE: Verificar existencias directamente en PostgreSQL.")


if __name__ == "__main__":
    main()
