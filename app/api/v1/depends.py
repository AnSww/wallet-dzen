from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper


async def get_session() -> AsyncSession:
    async for s in db_helper.session_getter():
        yield s


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session
