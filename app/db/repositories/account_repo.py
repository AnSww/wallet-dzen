from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.models import Account, User
from app.db.types import AccountType


class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(
            self,
            user_id: int,
            include_archived: bool = False,
            limit: int = 100,
            offset: int = 0,
    ) -> list[Account]:
        stmt = (
            select(Account)
            .where(Account.user_id == user_id)
            .order_by(Account.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if not include_archived:
            stmt = stmt.where(Account.archived == False)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_owned(self, user_id: int, account_id: int) -> Account | None:
        stmt = select(Account).where(Account.user_id == user_id, Account.id == account_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(
            self,
            *,
            user: User,
            name: str,
            currency: str,
            type_: AccountType,
            initial_balance: Decimal | None = None,
    ) -> Account:
        acc = Account(
            user_id=user.id,
            name=name,
            currency=currency,
            type=type_,
            balance=initial_balance or 0,
            archived=False,
        )
        self.session.add(acc)
        await self.session.flush()  # чтобы получить acc.id
        return acc

    async def patch(
            self,
            *,
            account: Account,
            name: str | None = None,
            archived: bool | None = None,
    ) -> Account:
        if name is not None:
            account.name = name
        if archived is not None:
            account.archived = archived
        await self.session.flush()
        return account

    async def archive(self, *, account: Account) -> None:
        if not account.archived:
            account.archived = True
            await self.session.flush()