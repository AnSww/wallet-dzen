from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.config import settings

class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
        )
        self.session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine,
        )

db_helper = DataBaseHelper(url=settings.db_url, echo=settings.db_echo)