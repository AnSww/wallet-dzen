from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str = "sqlite+aiosqlite:///wallet-dzen.db"
    db_echo: bool = True


settings = Settings()

