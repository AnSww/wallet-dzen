from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Category
from app.db.types import CategoryKind


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int, category_id: str) -> Category | None:
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_name_kind(
        self, user_id: int, name: str, kind: CategoryKind
    ) -> Category | None:
        # уникальность имени в рамках (user, kind), безрегистрово
        stmt = select(Category).where(
            Category.user_id == user_id,
            Category.kind == kind,
            func.lower(Category.name) == func.lower(name),
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list(
        self,
        user_id: int,
        *,
        kind: CategoryKind | None = None,
        include_archived: bool = False,
        search: str | None = None,
        parent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Category]:
        cond = [Category.user_id == user_id]
        if not include_archived:
            cond.append(Category.archived.is_(False))
        if kind is not None:
            cond.append(Category.kind == kind)
        if parent_id is not None:
            cond.append(Category.parent_id == parent_id)
        if search:
            like = f"%{search.strip()}%"
            cond.append(
                func.unaccent(func.lower(Category.name)).like(
                    func.unaccent(func.lower(like))
                )
            )

        stmt = (
            select(Category)
            .where(and_(*cond))
            .order_by(Category.created_at.desc(), Category.id.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create(
        self,
        *,
        user_id: int,
        name: str,
        kind: CategoryKind,
        parent: Category | None = None,
    ) -> Category:
        cat = Category(
            user_id=user_id,
            name=name,
            kind=kind,
            parent_id=parent.id if parent else None,
        )
        self.session.add(cat)
        await self.session.flush()
        return cat

    async def update(
        self,
        category: Category,
        *,
        name: str | None = None,
        parent: Category | None = ...,
        archived: bool | None = None,
    ) -> Category:
        if name is not None:
            category.name = name
        if parent is not ...:  # отличаем "не передан" от "явно null"
            category.parent_id = parent.id if parent else None
        if archived is not None:
            category.archived = archived

        await self.session.flush()
        return category

    async def soft_delete(self, category: Category) -> None:
        category.archived = True
        await self.session.flush()

    async def archive_children(self, user_id: int, parent_id: str) -> int:
        stmt = (
            update(Category)
            .where(Category.user_id == user_id, Category.parent_id == parent_id)
            .values(archived=True)
            .execution_options(synchronize_session=False)
        )
        res = await self.session.execute(stmt)
        return res.rowcount or 0
