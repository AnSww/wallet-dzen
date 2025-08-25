from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


class ApiPrefix(BaseModel):
    prefix: str = "/api"


class DataConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    max_overflow: int = 10
    pool_size: int = 50


class AuthJWT(BaseModel):
    private_key_path: Path = PROJECT_ROOT / "app" / "certs" / "jwt-private.pem"
    public_key_path: Path = PROJECT_ROOT / "app" / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_ttl_min: int = 15
    refresh_ttl_min: int = 60 * 24 * 30


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()
    db: DataConfig
    jwt: AuthJWT = AuthJWT()


settings = Settings()
