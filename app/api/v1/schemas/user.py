from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime


class UserUpdate(BaseModel):
    name: str | None = None
    password: str | None = Field(default=None, min_length=8)
