from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import UserCreate, UserOut
from app.api.v1.depends import get_db
from app.db.repositories.user_repo import UserRepository
from app.core.security import hash_password

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
