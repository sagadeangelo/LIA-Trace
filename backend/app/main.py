
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="API de trazabilidad logistica e integracion ERP",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# En esta etapa no habilitamos origenes web externos.
# La configuracion CORS se definira al incorporar
# clientes web y sus dominios autorizados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/", tags=["System"])
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": "/docs",
    }
