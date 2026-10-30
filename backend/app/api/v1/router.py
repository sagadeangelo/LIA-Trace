
from fastapi import APIRouter

from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.movements import router as movements_router
from app.api.v1.endpoints.returns import router as returns_router


api_router = APIRouter()


@api_router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "LIA TRACE API",
        "version": "0.1.0",
    }


@api_router.get("/", tags=["System"])
def api_info():
    return {
        "message": "Bienvenido a LIA TRACE API",
        "api_version": "v1",
        "status": "development",
    }


api_router.include_router(inventory_router)
api_router.include_router(movements_router)
api_router.include_router(returns_router)
