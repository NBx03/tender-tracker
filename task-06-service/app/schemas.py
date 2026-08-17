from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.statuses import TenderStatus


class RequestModel(BaseModel):
    # Пробелы по краям срезаются до проверки длины, поэтому строка из пробелов
    # не проходит валидацию так же, как пустая.
    model_config = ConfigDict(str_strip_whitespace=True)


class TenderCreate(RequestModel):
    title: str = Field(min_length=1, max_length=500)
    changed_by: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class StatusUpdate(RequestModel):
    status: TenderStatus
    changed_by: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class Tender(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TenderStatus
    created_at: datetime


class StatusChange(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Пусто у записи о создании тендера.
    old_status: TenderStatus | None
    new_status: TenderStatus
    changed_by: str
    reason: str
    changed_at: datetime
