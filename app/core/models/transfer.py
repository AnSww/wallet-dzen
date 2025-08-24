from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Transfer(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    from_account_id: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    to_account_id: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    amount: Mapped[str] = mapped_column(Numeric(14, 2))
    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    occurred_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    user: Mapped["User"] = relationship(back_populates="transfers")
    from_account: Mapped["Account"] = relationship(foreign_keys=[from_account_id], back_populates="outgoing_transfers")
    to_account: Mapped["Account"] = relationship(foreign_keys=[to_account_id], back_populates="incoming_transfers")
