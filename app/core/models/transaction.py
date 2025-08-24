from datetime import datetime
from decimal import Decimal

from app.db import Base
from sqlalchemy import String, Enum, ForeignKey, Boolean, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.types import Direction


class Transaction(Base):
    user_id = Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"), nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    direction: Enum = mapped_column(Enum(Direction, name="direction"), create_type=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    occurred_at: Mapped[datetime] = mapped_column()  # клиент задаёт время операции

    user: Mapped["User"] = relationship(back_populates="accounts")
    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")
