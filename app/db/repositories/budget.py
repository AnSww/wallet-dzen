from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from pydantic.dataclasses import dataclass
from sqlalchemy import select, delete, literal_column, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.models import Budget, User, Transaction
from app.db.types import Direction


@dataclass
class BudgetUpsertItem:
    category_id: int
    amount: Decimal


class BudgetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_owned(self, *, user_id: int, budget_id: int) -> Budget | None:
        stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_month_plans(self, *, user_id: int, month: date) -> list[Budget]:
        month = month.replace(day=1)
        stmt = (
            select(Budget)
            .where(Budget.user_id == user_id, Budget.month == month)
            .order_by(Budget.category_id.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars())

    async def create(
        self, *, user: User, category_id: int, amount: Decimal, month: date
    ) -> Budget:
        obj = Budget(
            user_id=user.id,
            category_id=category_id,
            amount=amount,
            month=month.replace(day=1),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def patch(
        self,
        *,
        budget: Budget,
        category_id: int | None = None,
        amount: Decimal | None = None,
        month: date | None = None,
    ) -> Budget:
        if category_id is not None:
            budget.category_id = category_id
        if amount is not None:
            budget.amount = amount
        if month is not None:
            budget.month = month.replace(day=1)
        await self.session.flush()
        return budget

    async def delete_owned(self, *, user_id: int, budget_id: int) -> int:
        stmt = (
            delete(Budget)
            .where(Budget.id == budget_id, Budget.user_id == user_id)
            .returning(Budget.id)
        )
        res = await self.session.execute(stmt)
        return len(res.fetchall())

    async def bulk_upsert_month(
        self, *, user_id: int, month: date, items: Iterable[BudgetUpsertItem]
    ) -> None:
        """
        Вставка/обновление по уникальному ключу (user_id, month, category_id).
        Требует уникального индекса в БД.
        """
        month = month.replace(day=1)
        rows = [
            {
                "user_id": user_id,
                "category_id": it.category_id,
                "month": month,
                "amount": it.amount,
            }
            for it in items
        ]
        if not rows:
            return
        stmt = (
            pg_insert(Budget)
            .values(rows)
            .on_conflict_do_update(
                index_elements=[Budget.user_id, Budget.month, Budget.category_id],
                set_={"amount": literal_column("excluded.amount")},
            )
        )
        await self.session.execute(stmt)

    # --- агрегации ---

    async def month_actuals_by_category(
        self, *, user_id: int, month: date, account_id: int | None = None
    ) -> dict[int, Decimal]:
        """
        Факт расходов (direction='out') за месяц по категориям.
        Возвращает {category_id: actual_sum}.
        """
        month = month.replace(day=1)
        month_next = (month.replace(day=28) + timedelta(days=4)).replace(
            day=1
        )  # первое число след. месяца

        where = [
            Transaction.user_id == user_id,
            (
                Transaction.direction == Direction.outgoing
                if hasattr(Direction, "outgoing")
                else "out"
            ),
            Transaction.occurred_at >= month,
            Transaction.occurred_at < month_next,
        ]
        if account_id is not None:
            where.append(Transaction.account_id == account_id)

        stmt = (
            select(
                Transaction.category_id, func.coalesce(func.sum(Transaction.amount), 0)
            )
            .where(and_(*where))
            .group_by(Transaction.category_id)
        )
        res = await self.session.execute(stmt)
        out: dict[int, Decimal] = {}
        for cat_id, total in res.all():
            if cat_id is not None:
                out[int(cat_id)] = Decimal(total)
        return out
