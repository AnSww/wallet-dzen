from fastapi import APIRouter
from app.api.v1.depends import get_db
from app.db.repositories.user_repo import UserRepository

router = APIRouter(tags=["user"])


@router.get("/{user_id}")
async def get_user(user_id: int, session):
    return await UserRepository.get_by_id(user_id)
