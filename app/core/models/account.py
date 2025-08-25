from sqlalchemy import String, ForeignKey, Enum, Boolean, Float, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db import Base
from app.db.types import AccountType
from .mixins import UserRelationMixin


class Account(UserRelationMixin, Base):
    _user_back_populates = "accounts"
    name: Mapped[str] = mapped_column(String(length=120))
    currency: Mapped[str] = mapped_column(String(length=3))
    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type", create_type=False)
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    outgoing_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="from_account",
        foreign_keys="Transfer.from_account_id",
        cascade="all, delete-orphan",
    )
    incoming_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="to_account",
        foreign_keys="Transfer.to_account_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq__account__user_name"),
    )
