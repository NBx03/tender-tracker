from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection, Row

_INSERT_TENDER = text("""
    INSERT INTO tenders (title)
    VALUES (:title)
    RETURNING id, title, status, created_at
""")

_LOCK_TENDER = text("""
    SELECT id, title, status, created_at
    FROM tenders
    WHERE id = :tender_id
    FOR UPDATE
""")

_SELECT_TENDER = text("""
    SELECT id, title, status, created_at
    FROM tenders
    WHERE id = :tender_id
""")

_SELECT_HISTORY = text("""
    SELECT old_status, new_status, changed_by, reason, changed_at
    FROM tender_status_history
    WHERE tender_id = :tender_id
    ORDER BY changed_at, id
""")

_UPDATE_STATUS = text("""
    UPDATE tenders
    SET status = CAST(:new_status AS tender_status)
    WHERE id = :tender_id
    RETURNING id, title, status, created_at
""")

_INSERT_HISTORY = text("""
    INSERT INTO tender_status_history
        (tender_id, old_status, new_status, changed_by, reason)
    VALUES (
        :tender_id,
        CAST(:old_status AS tender_status),
        CAST(:new_status AS tender_status),
        :changed_by,
        :reason
    )
""")


def create_tender(
    connection: Connection,
    title: str,
    changed_by: str,
    reason: str,
) -> Row:
    tender = connection.execute(_INSERT_TENDER, {"title": title}).one()
    # Первая запись истории: старого статуса нет, тендер только появился.
    connection.execute(
        _INSERT_HISTORY,
        {
            "tender_id": tender.id,
            "old_status": None,
            "new_status": tender.status,
            "changed_by": changed_by,
            "reason": reason,
        },
    )
    return tender


def get_tender(connection: Connection, tender_id: int) -> Row | None:
    return connection.execute(_SELECT_TENDER, {"tender_id": tender_id}).one_or_none()


def select_history(connection: Connection, tender_id: int) -> Sequence[Row]:
    # Сортировка по времени и по идентификатору: две записи одного тендера
    # могут получить одинаковое время, и тогда порядок задаёт идентификатор.
    return connection.execute(_SELECT_HISTORY, {"tender_id": tender_id}).all()


def lock_tender(connection: Connection, tender_id: int) -> Row | None:
    # FOR UPDATE держит строку до конца транзакции. Второй одновременный
    # запрос ждёт здесь и после ожидания читает уже изменённый статус,
    # поэтому проверяет переход от актуального значения.
    return connection.execute(_LOCK_TENDER, {"tender_id": tender_id}).one_or_none()


def change_status(
    connection: Connection,
    tender_id: int,
    old_status: str,
    new_status: str,
    changed_by: str,
    reason: str,
) -> Row:
    tender = connection.execute(
        _UPDATE_STATUS,
        {"tender_id": tender_id, "new_status": new_status},
    ).one()
    connection.execute(
        _INSERT_HISTORY,
        {
            "tender_id": tender_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by,
            "reason": reason,
        },
    )
    return tender
