from datetime import date, datetime
from decimal import Decimal

from pydantic import condecimal, BaseModel, field_validator, Field

Money = condecimal(gt=0, max_digits=14, decimal_places=2)


def _month_floor(d: date | datetime) -> date:
    d = d.date() if isinstance(d, datetime) else d
    return d.replace(day=1)


class BudgetBase(BaseModel):
    category_id: int = Field(..., ge=1)
    month: date
    amount: Money

    @field_validator("month", mode="before")
    @classmethod
    def normalize_month(cls, v):
        if isinstance(v, str):
            v = date.fromisoformat(v)  # "2025-08-01"
        return _month_floor(v)


class BudgetPut(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    category_id: int | None = Field(None, ge=1)
    month: date | None
    amount: Money | None

    @field_validator("month", mode="before")
    @classmethod
    def normalize_month(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            v = date.fromisoformat(v)
        return _month_floor(v)


class BudgetOut(BudgetBase):
    budget_id: int
    user_id: int

    class Config:
        from_attributes = True
        populate_by_name = True


class BudgetFactItem(BaseModel):
    category_id: int
    planned: Decimal = Field(..., max_digits=14, decimal_places=2)
    actual: Decimal = Field(..., max_digits=14, decimal_places=2)
    delta: Decimal = Field(..., max_digits=14, decimal_places=2)


class BudgetMonthOut(BaseModel):
    month: date
    items: list[BudgetFactItem]
    totals: dict[str, Decimal]
