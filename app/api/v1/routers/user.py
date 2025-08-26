from fastapi import APIRouter
from app.api.v1.depends import get_db
from app.db.repositories.user_repo import UserRepository

router = APIRouter(tags=["user"])
