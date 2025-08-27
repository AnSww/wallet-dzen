from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, or_, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Account, Category, Transaction
from app.db.types import Direction, CategoryKind
from app.utils.cursor import decode_cursor, encode_cursor


class InsufficientFunds(Exception): ...


class Forbidden(Exception): ...


class NotFound(Exception): ...


class Conflict(Exception): ...


class ValidationError(Exception): ...


class TransactionRepository:
    def __init__(self, session: AsyncSession, enforce_non_negative: bool = False):
        self.session = session
        self.enforce_non_negative = enforce_non_negative

    async def _ensure_account(self, user_id: int, account_id: int) -> Account:
        q = select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
            Account.archived == False,
        )
        acc = (await self.session.execute(q)).scalar_one_or_none()
        if not acc:
            raise NotFound("account")
        return acc

    async def _ensure_category(
        self, user_id: int, category_id: int | None
    ) -> Category | None:
        if category_id is None:
            return None
        q = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.archived == False,
        )
        cat = (await self.session.execute(q)).scalar_one_or_none()
        if not cat:
            raise NotFound("category")
        return cat

    async def _apply_balance_delta(self, user_id: int, account_id: int, delta: Decimal):

        stmt = (
            update(Account)
            .where(Account.id == account_id, Account.user_id == user_id)
            .values(balance=Account.balance + delta)
        )
        if self.enforce_non_negative and delta < 0:
            stmt = stmt.where(Account.balance >= -delta)

        result = await self.session.execute(stmt)
        if result.rowcount != 1:
            raise InsufficientFunds()

    async def get(self, user_id: int, tx_id: int) -> Transaction:
        q = select(Transaction).where(
            Transaction.id == tx_id, Transaction.user_id == user_id
        )
        tx = (await self.session.execute(q)).scalar_one_or_none()
        if not tx:
            raise NotFound("transaction")
        return tx

    async def list(
        self,
        user_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
        account_id: int | None = None,
        category_id: int | None = None,
        direction: Direction | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        search: str | None = None,
    ) -> tuple[list[Transaction], str | None]:
        limit = min(max(limit, 1), 100)

        q = select(Transaction).where(Transaction.user_id == user_id)

        if account_id:
            q = q.where(Transaction.account_id == account_id)
        if category_id:
            q = q.where(Transaction.category_id == category_id)
        if direction:
            q = q.where(Transaction.direction == direction)
        if date_from:
            q = q.where(Transaction.occurred_at >= date_from)
        if date_to:
            q = q.where(Transaction.occurred_at < date_to)
        if min_amount is not None:
            q = q.where(Transaction.amount >= min_amount)
        if max_amount is not None:
            q = q.where(Transaction.amount <= max_amount)
        if search:
            q = q.where(Transaction.note.ilike(f"%{search}%"))

        if cursor:
            ca, cid = decode_cursor(cursor)
            q = q.where(
                or_(
                    Transaction.created_at < ca,
                    and_(Transaction.created_at == ca, Transaction.id < cid),
                )
            )

        q = q.order_by(desc(Transaction.created_at), desc(Transaction.id)).limit(
            limit + 1
        )
        res = (await self.session.execute(q)).scalars().all()

        next_cursor = None
        if len(res) > limit:
            last = res[limit - 1]
            next_cursor = encode_cursor(last.created_at, last.id)
            res = res[:limit]
        return res, next_cursor

    async def create(
        self,
        user_id: int,
        *,
        account_id: int,
        category_id: int | None,
        direction: Direction,
        amount: Decimal,
        note: str | None,
        occurred_at: datetime,
    ) -> Transaction:
        acc = await self._ensure_account(user_id, account_id)
        cat = await self._ensure_category(user_id, category_id)

        # category kind ↔ direction совместимость
        if cat:
            if direction == Direction.outgoing and cat.kind != CategoryKind.expense:
                raise ValidationError("expense category required for outgoing tx")
            if direction == Direction.incoming and cat.kind != CategoryKind.income:
                raise ValidationError("income category required for incoming tx")

        tx = Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            direction=direction,
            amount=amount,
            note=note,
            occurred_at=occurred_at,
        )
        self.session.add(tx)
        await self.session.flush()

        if self.enforce_non_negative and direction == Direction.outgoing:
            stmt = (
                update(Account)
                .where(
                    Account.id == acc.id,
                    Account.user_id == user_id,
                    Account.balance >= amount,
                )
                .values(balance=Account.balance - amount)
            )
            result = await self.session.execute(stmt)
            if result.rowcount != 1:
                raise InsufficientFunds()
        else:
            delta = amount if direction == Direction.incoming else -amount
            stmt = (
                update(Account)
                .where(Account.id == acc.id, Account.user_id == user_id)
                .values(balance=Account.balance + delta)
            )
            await self.session.execute(stmt)

        return tx

    async def update(
        self,
        user_id: int,
        tx_id: int,
        *,
        account_id: int | None = None,
        category_id: int | None = None,
        direction: Direction | None = None,
        amount: Decimal | None = None,
        note: str | None = None,
        occurred_at: datetime | None = None,
    ) -> Transaction:
        q = select(Transaction).where(
            Transaction.id == tx_id, Transaction.user_id == user_id
        )
        tx = (await self.session.execute(q)).scalar_one_or_none()
        if not tx:
            raise NotFound("transaction")

        old_account_id = tx.account_id
        old_direction = tx.direction
        old_amount = tx.amount

        if direction and direction != old_direction:
            raise Conflict("changing direction is not allowed")

        if account_id is not None:
            await self._ensure_account(user_id, account_id)
        target_category_id = category_id if category_id is not None else tx.category_id
        cat = await self._ensure_category(user_id, target_category_id)
        if cat:
            need_kind = (
                CategoryKind.expense
                if old_direction == Direction.outgoing
                else CategoryKind.income
            )
            if cat.kind != need_kind:
                raise ValidationError("category kind mismatch")

        if account_id is not None:
            tx.account_id = account_id
        if category_id is not None:
            tx.category_id = category_id
        if amount is not None:
            tx.amount = amount
        if note is not None:
            tx.note = note
        if occurred_at is not None:
            tx.occurred_at = occurred_at

        await self.session.flush()

        new_account_id = tx.account_id
        new_amount = tx.amount

        if new_account_id == old_account_id:
            if new_amount != old_amount:
                if old_direction == Direction.incoming:
                    delta = new_amount - old_amount
                else:
                    delta = old_amount - new_amount
                await self._apply_balance_delta(user_id, new_account_id, delta)
        else:
            delta_old = (
                -old_amount if old_direction == Direction.incoming else +old_amount
            )
            await self._apply_balance_delta(user_id, old_account_id, delta_old)
            delta_new = (
                +new_amount if old_direction == Direction.incoming else -new_amount
            )
            await self._apply_balance_delta(user_id, new_account_id, delta_new)

        return tx

    async def delete(self, user_id: int, tx_id: int) -> None:
        tx = await self.get(user_id, tx_id)
        delta = (-tx.amount) if tx.direction == Direction.incoming else (+tx.amount)
        stmt = (
            update(Account)
            .where(Account.id == tx.account_id, Account.user_id == user_id)
            .values(balance=Account.balance + delta)
        )
        await self.session.execute(stmt)
        await self.session.delete(tx)
