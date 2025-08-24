from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.db.types import Role


class User(Base):
    email: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(length=255))
    name: Mapped[str] = mapped_column(String(length=120))
    role: Mapped[Role] = mapped_column(Enum(Role, name="role", create_type=False), default=Role.user)