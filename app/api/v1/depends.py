from typing import Annotated

from fastapi import Depends, HTTPException, status, Request, Security
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.schemas.user import UserOut
from app.core.security import decode_token


from app.db import db_helper
from app.db.repositories.user_repo import UserRepository

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ACCESS_COOKIE_NAME = "access"
REFRESH_COOKIE_NAME = "refresh"
bearer_scheme = HTTPBearer(auto_error=False)

async def get_session() -> AsyncSession:
    async for s in db_helper.session_getter():
        yield s


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


def _unauthorized(msg: str) -> None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)


async def get_token_from_cookie_or_header(
    request: Request,
    cookie_type: str,
    bearer: HTTPAuthorizationCredentials | None = None,
) -> str | None:
    token_cookie = request.cookies.get(cookie_type)
    if token_cookie:
        return token_cookie
    if bearer and bearer.scheme.lower() == "bearer":
        return bearer.credentials
    _unauthorized("missing credentials")



async def get_current_token_payload_from_cookie(
    request: Request,
    cookie_type: str = ACCESS_COOKIE_NAME,
) -> dict | None:
    token = await get_token_from_cookie_or_header(request, cookie_type)
    try:
        payload = decode_token(token=token)
        return payload
    except InvalidTokenError as e:
        _unauthorized(f"invalid token error: {e}")



async def get_access_payload(
    payload: dict = Depends(get_current_token_payload_from_cookie),
) -> dict:
    return payload


async def get_refresh_payload(request: Request) -> dict:
    return await get_current_token_payload_from_cookie(request, REFRESH_COOKIE_NAME)


def validate_token_type(payload: dict, token_type: str) -> bool:
    current_token_type = payload.get('type')
    if current_token_type == token_type:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"invalid token type {current_token_type!r} expected {token_type!r}",
    )


async def get_user_by_token_sub(payload: dict, session: AsyncSession = Depends(get_session)):
    user_id: int | None = int(payload.get("sub"))
    user = await UserRepository(session).get_by_id(user_id)
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )


def get_current_token_payload(
    payload: dict = Depends(get_access_payload),
) -> dict:
    return payload


class UserGetterFromToken:
    def __init__(self, token_type: str):
        self.token_type = token_type

    async def __call__(self, request: Request, session: AsyncSession = Depends(get_session)):
        payload = await get_current_token_payload_from_cookie(request, self.token_type)
        validate_token_type(payload, self.token_type)

        user_id = payload.get("sub")
        return await UserRepository(session).get_by_id(int(user_id))



get_current_user = UserGetterFromToken(ACCESS_COOKIE_NAME)
get_user_by_refresh = UserGetterFromToken(REFRESH_COOKIE_NAME)