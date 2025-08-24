from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.routers.auth import router as auth_router
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base, db_helper
import uvicorn
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    await db_helper.dispose()


main_app = FastAPI(lifespan=lifespan)
main_app.include_router(auth_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", host=settings.run.host, port=settings.run.port, reload=True
    )
