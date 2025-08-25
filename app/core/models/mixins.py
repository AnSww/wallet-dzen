from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import declared_attr, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class UserRelationMixin:
    _user_id_ondelete: str = "CASCADE"
    _user_id_unique: bool = False
    _user_back_populates: str | None = None
    _user_index: bool = True

    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(
            ForeignKey("users.id", ondelete=cls._user_id_ondelete),
            unique=cls._user_id_unique,
            index=cls._user_index,
        )

    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            back_populates=cls._user_back_populates,
        )
