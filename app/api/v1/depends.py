from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token


from app.db import db_helper
from app.db.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_session() -> AsyncSession:
    async for s in db_helper.session_getter():
        yield s


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise unauthorized
        user_id = int(payload["sub"])
    except Exception:
        raise unauthorized

    user = await UserRepository(session).get_by_id(user_id)
    if not user:
        raise unauthorized
    return user
