
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

URL = "http://localhost:8000/api/v1/movements"

CLAVE = "LIA-IDEMP-DOS-ARTICULOS-001"

barrier = Barrier(2)


def enviar_solicitud(articulo_id):
    payload = {
        "inventory_item_id": articulo_id,
        "movement_type": "ENTRY",
        "quantity": 1,
        "reference": "PRUEBA-DOS-ARTICULOS-001",
        "idempotency_key": CLAVE,
    }

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
            resultado = json.loads(
                response.read().decode("utf-8")
            )

            return {
                "articulo": articulo_id,
                "http": response.status,
                "movimiento_id": resultado.get("id"),
                "clave": resultado.get("idempotency_key"),
            }

    except urllib.error.HTTPError as error:
        return {
            "articulo": articulo_id,
            "http": error.code,
            "mensaje": error.read().decode("utf-8"),
        }

    except Exception as error:
        return {
            "articulo": articulo_id,
            "error": str(error),
        }


def main():
    print("PRUEBA DE CONCURRENCIA ENTRE DOS ARTICULOS")
    print("Clave:", CLAVE)
    print("-----------------------------------------")

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(
            executor.map(enviar_solicitud, [1, 3])
        )

    for resultado in resultados:
        print(resultado)

    exitosos = [
        r for r in resultados
        if r.get("http") in (200, 201)
    ]

    conflictos = [
        r for r in resultados
        if r.get("http") == 409
    ]

    print("-----------------------------------------")
    print("Solicitudes exitosas:", len(exitosos))
    print("Conflictos HTTP 409:", len(conflictos))

    if len(exitosos) == 1 and len(conflictos) == 1:
        print("RESULTADO: Comportamiento esperado.")
    else:
        print("RESULTADO: Requiere revision.")

    print("IMPORTANTE: Verificar existencias en PostgreSQL.")


if __name__ == "__main__":
    main()
