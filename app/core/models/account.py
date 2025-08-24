from sqlalchemy import String, ForeignKey, Enum, Boolean, Float, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db import Base
from app.db.types import AccountType


class Account(Base):
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(length=120))
    currency: Mapped[str] = mapped_column(String(length=3))
    type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type", create_type=False))
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)


    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account", cascade="all, delete-orphan")
