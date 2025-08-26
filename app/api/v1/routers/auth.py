from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.v1.schemas.user import UserCreate, UserOut, TokenPair
from app.api.v1.depends import (
    get_current_user,
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    get_refresh_payload,
)
from app.db.db_helper import get_session
from app.db.repositories.user_repo import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(
    response: Response,
    *,
    name: str,
    value: str,
    max_age_sec: int,
    httponly: bool = True,
    path: str = "/",
):
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age_sec,
        expires=max_age_sec,
        httponly=httponly,
        secure=settings.cookies.secure,
        samesite=settings.cookies.samesite,
        path=path,
    )


def _clear_cookie(response: Response, name: str, path: str = "/"):
    response.delete_cookie(
        key=name,
        path=path,
        httponly=True,
        secure=settings.cookies.secure,
        samesite=settings.cookies.samesite,
    )


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    repo = UserRepository(session)
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = await repo.create(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    await session.commit()
    return user


@router.post("/login", response_model=TokenPair)
async def login(
    payload: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    _set_cookie(
        response,
        name=ACCESS_COOKIE_NAME,
        value=access,
        max_age_sec=settings.jwt.access_ttl_min * 60,
        httponly=True,
    )
    _set_cookie(
        response,
        name=REFRESH_COOKIE_NAME,
        value=refresh,
        max_age_sec=settings.jwt.refresh_ttl_min * 60,
        httponly=True,
        # path="/api/v1/auth",  # refresh читаем только под /auth
    )

    return {"access_token": access, "refresh_token": refresh}


@router.post("/refresh", status_code=200)
async def refresh(
    request: Request, response: Response, payload=Depends(get_refresh_payload)
):

    user_id = payload.get("user_id")

    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(
        user_id
    )  # без БД смысла ротации немного, но пусть будет...

    _set_cookie(
        response,
        name=ACCESS_COOKIE_NAME,
        value=new_access,
        max_age_sec=settings.jwt.access_ttl_min * 60,
        httponly=True,
    )
    _set_cookie(
        response,
        name=REFRESH_COOKIE_NAME,
        value=new_refresh,
        max_age_sec=settings.jwt.refresh_ttl_min * 60,
        httponly=True,
        path="/api/v1/auth",
    )

    return {"detail": "refreshed"}


@router.post("/logout", status_code=204)
async def logout(response: Response):
    _clear_cookie(response, ACCESS_COOKIE_NAME)
    _clear_cookie(response, REFRESH_COOKIE_NAME)
    return


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
