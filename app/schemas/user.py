import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    
    @field_validator("password")
    @classmethod
    def password_must_have_letter_and_digit(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Parola trebuie să conțină cel puțin o cifră")
        if not any(c.isalpha() for c in v):
            raise ValueError("Parola trebuie să conțină cel puțin o literă")
        return v

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime