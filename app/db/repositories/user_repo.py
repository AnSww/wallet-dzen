from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        res = await self.session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: EmailStr) -> User | None:
        res = await self.session.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def list(self, limit: int = 50, offset: int = 0) -> list[User]:
        res = await self.session.execute(
            select(User).order_by(User.id).limit(limit).offset(offset)
        )
        return list(res.scalars().all())

    async def create(self, *, email: EmailStr, name: str, password_hash: str) -> User:
        user = User(email=email, name=name, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(
        self,
        user: User,
        *,
        name: str | None = None,
        password_hash: str | None = None,
    ) -> User:
        if name is not None:
            user.name = name
        if password_hash is not None:
            user.password_hash = password_hash
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
