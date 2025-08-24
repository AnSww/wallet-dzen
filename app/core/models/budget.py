from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Budget(Base):
    """Бюджет на месяц по категории расхода (planned). Факт считаем из Transaction."""

    user_id: Mapped[str] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[str] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[date]  # convention: первое число месяца
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category"] = relationship()
