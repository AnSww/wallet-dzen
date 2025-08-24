from app.db import Base
from sqlalchemy import String, Enum, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.types import CategoryKind


class Category(Base):
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[CategoryKind] = mapped_column(Enum(CategoryKind, name="category_kind", create_type=False))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="categories")
    parent: Mapped["Category | None"] = relationship(remote_side="Category.id")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
