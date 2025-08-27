from datetime import datetime
from decimal import Decimal

from app.db import Base
from sqlalchemy import String, Enum, ForeignKey, DateTime, Numeric, text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.types import Direction
from .mixins import UserRelationMixin


class Transaction(UserRelationMixin, Base):
    _user_back_populates = "transactions"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    direction: Mapped[Direction] = mapped_column(
        Enum(Direction, name="direction", create_type=False)
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("TIMEZONE('UTC', NOW())")
    )

    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")
