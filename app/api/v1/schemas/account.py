from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.db.types import AccountType


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=4, max_length=16)
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="ISO-4217, например: RUB, EUR")
    type: AccountType
    initial_balance: Decimal = Field(
        default=0, ge=0)


class AccountPatch(BaseModel):
    name: str | None = Field(default=None, min_length=4, max_length=16)
    archived: bool = False


class AccountOut(BaseModel):
    id: int
    name: str
    currency: str
    type: AccountType
    archived: bool
    balance: Decimal
    created_at: datetime

    class Config:
        from_attributes = True