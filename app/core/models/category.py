from app.db import Base
from sqlalchemy import String, Enum, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.types import CategoryKind
from .mixins import UserRelationMixin


class Category(UserRelationMixin, Base):
    _user_back_populates = "categories"

    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[CategoryKind] = mapped_column(
        Enum(CategoryKind, name="category_kind", create_type=False)
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
