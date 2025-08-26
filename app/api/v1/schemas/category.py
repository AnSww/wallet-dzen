from datetime import datetime

from pydantic import BaseModel, Field

from app.db.types import CategoryKind


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    kind: CategoryKind
    parent_id: str | None = Field(default=None)


class CategoryCreate(CategoryBase):
    """Создание категории. kind обязателен, менять его потом нельзя."""


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    parent_id: str | None = Field(default=None)
    archived: bool | None = None
    # kind менять нельзя — если нужно, создай новую категорию и перенеси транзакции


class CategoryOut(BaseModel):
    id: str
    user_id: str
    name: str
    kind: CategoryKind
    parent_id: str | None = None
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True
