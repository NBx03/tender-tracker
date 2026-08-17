from typing import Annotated

from fastapi import Depends, FastAPI, status
from sqlalchemy.engine import Connection

from app import repository
from app.db import get_connection
from app.schemas import Tender, TenderCreate

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
