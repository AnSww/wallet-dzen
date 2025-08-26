from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.routers.auth import router as auth_router

from app.api.v1.routers.account import router as account_router
from app.api.v1.routers.category import router as category_router
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handler import http_exception_handler, unhandled_error_handler
from app.db import Base, db_helper
import uvicorn
from core.config import settings
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    await db_helper.dispose()


main_app = FastAPI(lifespan=lifespan)
main_app.add_exception_handler(StarletteHTTPException, http_exception_handler)
main_app.add_exception_handler(Exception, unhandled_error_handler)

main_app.include_router(auth_router)
main_app.include_router(account_router)
main_app.include_router(category_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", host=settings.run.host, port=settings.run.port, reload=True
    )
