from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


def get_connection() -> Iterator[Connection]:
    # Одна транзакция на запрос: engine.begin фиксирует её при обычном выходе
    # и откатывает при исключении. Смена статуса и запись в историю не могут
    # разойтись.
    with engine.begin() as connection:
        yield connection
