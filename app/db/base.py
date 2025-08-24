from datetime import datetime

from sqlalchemy import MetaData, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

from app.utils.case_converter import camel_case_to_snake_case


convention = {
    "ix": "ix__%(table_name)s__%(column_0_N_label)s",
    "uq": "uq__%(table_name)s__%(column_0_N_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_N_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s",
}
metadata = MetaData(naming_convention=convention)


def pluralize(name: str) -> str:
    if name.endswith(("s", "x", "z")) or name.endswith(("ch", "sh")):
        return name + "es"
    if name.endswith("y") and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    return name + "s"


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = metadata

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP")
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return pluralize(camel_case_to_snake_case(cls.__name__))
