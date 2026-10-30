
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Copiar configuracion del proyecto
COPY pyproject.toml ./

# Copiar codigo del backend
COPY app ./app

# Copiar pruebas automaticas
COPY tests ./tests

# Archivos necesarios para las migraciones
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Instalar dependencias principales y de desarrollo
RUN pip install --no-cache-dir ".[dev]"

# Ejecutar la aplicacion con usuario sin privilegios
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
