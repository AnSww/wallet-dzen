from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings


class DataBaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        max_overflow: int = 10,
        pool_size: int = 5,
    ):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            max_overflow=max_overflow,
            pool_size=pool_size,
        )
        self.session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session

async def get_session() -> AsyncSession:
    async for s in db_helper.session_getter():
        yield s


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session

db_helper = DataBaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    max_overflow=settings.db.max_overflow,
    pool_size=settings.db.pool_size,
)
