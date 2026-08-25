import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import ApplicationStatus

MAX_CUSTOM_FIELDS = 5
MAX_KEY_LENGTH = 50
ALLOWED_VALUE_TYPES = (str, int, float, bool)


def _validate_custom_fields(value: dict[str, Any]) -> dict[str, Any]:
    if len(value) > MAX_CUSTOM_FIELDS:
        raise ValueError(
            f"custom_fields nu poate avea mai mult de {MAX_CUSTOM_FIELDS} chei"
        )
    for key, val in value.items():
        if len(key) > MAX_KEY_LENGTH:
            raise ValueError(f"cheia '{key}' depășește {MAX_KEY_LENGTH} de caractere")
        if not isinstance(val, ALLOWED_VALUE_TYPES):
            raise ValueError(
                f"valoarea pentru '{key}' trebuie să fie str, int, float sau bool"
            )
    return value


class JobApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    job_url: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=5000)
    applied_date: date
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    @field_validator("custom_fields")
    @classmethod
    def validate_custom_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_custom_fields(value)


class JobApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=255)
    position: str | None = Field(default=None, min_length=1, max_length=255)
    job_url: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=5000)
    applied_date: date | None = None
    custom_fields: dict[str, Any] | None = None

    @field_validator("custom_fields")
    @classmethod
    def validate_custom_fields(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return value
        return _validate_custom_fields(value)


class JobApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class JobApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company: str
    position: str
    job_url: str | None
    notes: str | None
    status: ApplicationStatus
    applied_date: date
    custom_fields: dict[str, Any]
    version: int
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime