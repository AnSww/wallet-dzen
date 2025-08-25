from pydantic import EmailStr
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from app.db.types import Role


class User(Base):
    email: Mapped[EmailStr] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(length=255))
    name: Mapped[str] = mapped_column(String(length=120))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role", create_type=False), default=Role.user
    )

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
