from sqlalchemy import text
from sqlalchemy.engine import Connection, Row

_INSERT_TENDER = text("""
    INSERT INTO tenders (title)
    VALUES (:title)
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
