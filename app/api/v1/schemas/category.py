from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.types import CategoryKind


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    kind: CategoryKind
    parent_id: int | None = Field(default=None)


class CategoryCreate(CategoryBase):
    """Создание категории. kind обязателен, менять его потом нельзя."""

    @field_validator("parent_id", mode="before")
    @classmethod
    def zero_to_none(cls, v):
        if v in (0, "0", "", None):
            return None
        return v


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    parent_id: int | None = Field(default=None)
    archived: bool | None = False
    # kind менять нельзя — если нужно, создай новую категорию и перенеси транзакции

    @field_validator("parent_id", mode="before")
    @classmethod
    def zero_to_none(cls, v):
        if v in (0, "0", "", None):
            return None
        return v


class CategoryOut(BaseModel):
    id: int
    user_id: int
    name: str
    kind: CategoryKind
    parent_id: int | None = None
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True
