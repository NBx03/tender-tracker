import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

SERVICE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = SERVICE_DIR / "schema" / "01_schema.sql"


def _configured_url() -> str:
    """Строка подключения из окружения, иначе из .env."""
    from_environment = os.environ.get("DATABASE_URL")
    if from_environment:
        return from_environment

    env_file = SERVICE_DIR / ".env"
    if not env_file.exists():
        raise RuntimeError("Нужен DATABASE_URL в окружении или файл .env")

    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "DATABASE_URL":
            return value.strip()

    raise RuntimeError("В .env нет DATABASE_URL")


# Тесты работают с отдельной базой: имя рабочей с суффиксом _test. Переменная
# окружения выставляется до импорта приложения, потому что настройки читаются
# при импорте и движок создаётся сразу.
_BASE_URL = make_url(_configured_url())
_TEST_URL = _BASE_URL.set(database=f"{_BASE_URL.database}_test")
os.environ["DATABASE_URL"] = _TEST_URL.render_as_string(hide_password=False)


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    # CREATE DATABASE не выполняется внутри транзакции, поэтому AUTOCOMMIT.
    admin = create_engine(
        _TEST_URL.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{_TEST_URL.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{_TEST_URL.database}"'))
    admin.dispose()

    from app.db import engine

    with engine.begin() as connection:
        connection.exec_driver_sql(SCHEMA_FILE.read_text(encoding="utf-8"))

    yield

    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables() -> None:
    from app.db import engine

    # RESTART IDENTITY возвращает счётчики, чтобы идентификаторы в тестах были
    # предсказуемыми; CASCADE забирает историю по внешнему ключу.
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE tenders RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def tender(client) -> dict:
    response = client.post(
        "/tenders",
        json={
            "title": "Поставка серверного оборудования",
            "changed_by": "ivanov",
            "reason": "закупка подходит по профилю",
        },
    )
    assert response.status_code == 201
    return response.json()
