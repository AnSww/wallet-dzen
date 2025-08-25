from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Numeric,
    ForeignKey,
)
from .mixins import UserRelationMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Budget(UserRelationMixin, Base):
    """Бюджет на месяц по категории расхода (planned). Факт считаем из Transaction."""

    _user_back_populates = "budgets"

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[date]  # convention: первое число месяца
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    category: Mapped["Category"] = relationship()
