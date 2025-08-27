from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from pydantic.dataclasses import dataclass
from sqlalchemy import select, delete, literal_column, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.models import Budget, User, Transaction, Category


try:
    from app.db.types import Direction

    OUT = Direction.outgoing
except Exception:
    OUT = "out"


@dataclass
class BudgetUpsertItem:
    category_id: int
    amount: Decimal


class BudgetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _first_of_month(m: date) -> date:
        return m.replace(day=1)

    # --- CRUD ---
    async def get_owned(self, *, user_id: int, budget_id: int) -> Budget | None:
        stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(
        self, *, user_id: int, category_id: int, amount: Decimal, month: date
    ) -> Budget:
        obj = Budget(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            month=self._first_of_month(month),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def patch_owned(
        self,
        *,
        user_id: int,
        budget_id: int,
        category_id: int | None = None,
        amount: Decimal | None = None,
        month: date | None = None,
    ) -> Budget | None:
        obj = await self.get_owned(user_id=user_id, budget_id=budget_id)
        if not obj:
            return None
        if category_id is not None:
            obj.category_id = category_id
        if amount is not None:
            obj.amount = amount
        if month is not None:
            obj.month = self._first_of_month(month)
        await self.session.flush()
        return obj

    async def delete_owned(self, *, user_id: int, budget_id: int) -> int:
        stmt = (
            delete(Budget)
            .where(Budget.id == budget_id, Budget.user_id == user_id)
            .returning(Budget.id)
        )
        res = await self.session.execute(stmt)
        return len(res.fetchall())

    async def list_month_plans(self, *, user_id: int, month: date) -> list[Budget]:
        m = self._first_of_month(month)
        stmt = (
            select(Budget)
            .where(Budget.user_id == user_id, Budget.month == m)
            .order_by(Budget.category_id.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars())

    # --- Валидация категорий (расходные и принадлежат юзеру) ---
    async def validate_expense_categories(
        self, *, user_id: int, category_ids: list[int]
    ) -> None:
        if not category_ids:
            return
        q = select(Category.id, Category.kind).where(
            Category.user_id == user_id,
            Category.id.in_(category_ids),
        )
        res = await self.session.execute(q)
        found = {cid: kind for cid, kind in res.all()}
        missing = [cid for cid in category_ids if cid not in found]
        if missing:
            raise ValueError(f"categories_not_found: {missing}")

        wrong = [
            cid for cid, kind in found.items() if str(kind).split(".")[-1] != "expense"
        ]
        if wrong:
            raise ValueError(f"categories_not_expense: {wrong}")

    # --- Upsert набора бюджетов за месяц ---
    async def bulk_upsert_month(
        self, *, user_id: int, month: date, items: Iterable[BudgetUpsertItem]
    ) -> None:
        m = self._first_of_month(month)
        rows = [
            {
                "user_id": user_id,
                "category_id": i.category_id,
                "month": m,
                "amount": i.amount,
            }
            for i in items
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

    async def month_actuals_by_category(
        self, *, user_id: int, month: date, account_id: int | None = None
    ) -> dict[int, Decimal]:
        m = self._first_of_month(month)
        m_next = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
        conds = [
            Transaction.user_id == user_id,
            Transaction.direction == OUT,
            Transaction.occurred_at >= m,
            Transaction.occurred_at < m_next,
        ]
        if account_id is not None:
            conds.append(Transaction.account_id == account_id)

        stmt = (
            select(
                Transaction.category_id, func.coalesce(func.sum(Transaction.amount), 0)
            )
            .where(and_(*conds))
            .group_by(Transaction.category_id)
        )
        res = await self.session.execute(stmt)
        data: dict[int, Decimal] = {}
        for cat_id, total in res.all():
            if cat_id is not None:
                data[int(cat_id)] = Decimal(total)
        return data

    async def build_month_response(
        self, *, user_id: int, month: date, account_id: int | None = None
    ) -> dict:
        plans = await self.list_month_plans(user_id=user_id, month=month)
        actuals = await self.month_actuals_by_category(
            user_id=user_id, month=month, account_id=account_id
        )

        items: list[dict] = []
        total_planned = Decimal("0.00")
        total_actual = Decimal("0.00")

        for p in plans:
            planned = Decimal(p.amount)
            actual = Decimal(actuals.get(p.category_id, Decimal("0")))
            delta = planned - actual
            items.append(
                {
                    "category_id": p.category_id,
                    "planned": planned,
                    "actual": actual,
                    "delta": delta,
                }
            )
            total_planned += planned
            total_actual += actual

        return {
            "month": self._first_of_month(month),
            "items": items,
            "totals": {
                "planned": total_planned,
                "actual": total_actual,
                "delta": total_planned - total_actual,
            },
        }
