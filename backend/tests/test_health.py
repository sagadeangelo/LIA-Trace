
from fastapi.testclient import TestClient

from app.main import app


def test_openapi_disponible():
    """
    Verifica que LIA TRACE publica su documentacion OpenAPI.
    No modifica datos de inventario.
    """
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()

    assert data["info"]["title"] == "LIA_TRACE"
    assert data["info"]["version"] == "0.1.0"
