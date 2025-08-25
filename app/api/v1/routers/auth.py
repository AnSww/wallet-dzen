from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import UserCreate, UserOut, TokenPair
from app.api.v1.depends import get_db, get_current_user
from app.db.repositories.user_repo import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_db)):
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
async def login(payload: UserCreate, session: AsyncSession = Depends(get_db)):
    repo = UserRepository(session)
    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    jti = str(uuid4())
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id), jti=jti)
    # для простоты не храним refresh в БД;
    return {"access_token": access, "refresh_token": refresh}


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
