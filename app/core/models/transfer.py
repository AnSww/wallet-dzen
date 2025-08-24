from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from .mixins import UserRelationMixin


class Transfer(UserRelationMixin, Base):
    _user_back_populates = "transfers"

    from_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    to_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    occurred_at: Mapped[datetime]

    from_account: Mapped["Account"] = relationship(
        foreign_keys=[from_account_id], back_populates="outgoing_transfers"
    )
    to_account: Mapped["Account"] = relationship(
        foreign_keys=[to_account_id], back_populates="incoming_transfers"
    )
