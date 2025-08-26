from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, condecimal

from app.db.types import Direction


Money = condecimal(gt=0, max_digits=14, decimal_places=2)


class TransactionBase(BaseModel):
    account_id: str
    category_id: str | None = Field(default=None)
    direction: Direction
    amount: Money
    note: str | None = Field(default=None, max_length=500)
    occurred_at: datetime

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    account_id: str | None = None
    category_id: str | None  = None
    direction: Direction | None = None
    amount: Money | None = None
    note: str | None = Field(default=None, max_length=500)
    occurred_at: datetime | None = None

class TransactionOut(BaseModel):
    id: str
    user_id: str
    account_id: str
    category_id: str | None
    direction: Direction
    amount: Decimal
    note: str | None
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionsPage(BaseModel):
    items: list[TransactionOut]
    next_cursor: str | None = None