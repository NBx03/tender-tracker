from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.engine import Connection

from app import repository
from app.db import get_connection
from app.schemas import StatusUpdate, Tender, TenderCreate
from app.statuses import ALLOWED_TRANSITIONS, TenderStatus, is_allowed

app = FastAPI(title="Трекинг статусов тендеров")

DbConnection = Annotated[Connection, Depends(get_connection)]


@app.post("/tenders", response_model=Tender, status_code=status.HTTP_201_CREATED)
def create_tender(payload: TenderCreate, connection: DbConnection) -> Tender:
    tender = repository.create_tender(
        connection,
        title=payload.title,
        changed_by=payload.changed_by,
        reason=payload.reason,
    )
    return Tender.model_validate(tender)


@app.patch("/tenders/{tender_id}/status", response_model=Tender)
def update_status(
    tender_id: int,
    payload: StatusUpdate,
    connection: DbConnection,
) -> Tender:
    tender = repository.lock_tender(connection, tender_id)
    if tender is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тендер {tender_id} не найден",
        )

    current = TenderStatus(tender.status)
    if not is_allowed(current, payload.status):
        allowed = ", ".join(sorted(ALLOWED_TRANSITIONS[current])) or "нет"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Переход из «{current}» в «{payload.status}» недопустим. "
                f"Допустимые переходы из «{current}»: {allowed}"
            ),
        )

    updated = repository.change_status(
        connection,
        tender_id=tender_id,
        old_status=current,
        new_status=payload.status,
        changed_by=payload.changed_by,
        reason=payload.reason,
    )
    return Tender.model_validate(updated)
