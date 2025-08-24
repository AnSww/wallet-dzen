from sqlalchemy import MetaData
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


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = metadata

    id: Mapped[int] = mapped_column(primary_key=True)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{camel_case_to_snake_case(cls.__name__)}s"
