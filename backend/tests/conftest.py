
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import Settings


TEST_DATABASE_NAME = "lia_trace_test"


@pytest.fixture(scope="session")
def test_engine():
    """
    Crea una conexion exclusiva para pruebas.

    Nunca permite utilizar una base distinta
    de lia_trace_test.
    """

    original_url = make_url(Settings().DATABASE_URL)

    test_url = original_url.set(
        database=TEST_DATABASE_NAME
    )

    if test_url.database != TEST_DATABASE_NAME:
        raise RuntimeError(
            "SEGURIDAD: base de pruebas incorrecta."
        )

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            current_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if current_database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "SEGURIDAD: conexion a una base no autorizada."
            )

        yield engine

    finally:
        engine.dispose()
