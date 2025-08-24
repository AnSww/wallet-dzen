from datetime import datetime

from alembic.operations.toimpl import create_table
from sqlalchemy import String, ForeignKey, Enum, Boolean, Float, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.types import AccountType


class Account(Base):
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(length=120))
    currency: Mapped[str] = mapped_column(String(length=3))
    type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type", create_type=False))
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    user: Mapped["User"] = relationship(back_populates="accounts")