from pydantic import BaseModel
from pydantic_settings import BaseSettings

class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000

class ApiPrefix(BaseModel):
    prefix: str = '/api'

class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()

    db_url: str = "sqlite+aiosqlite:///wallet-dzen.db"
    db_echo: bool = True



settings = Settings()
