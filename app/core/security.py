from datetime import datetime, timezone, timedelta
from functools import lru_cache
from pathlib import Path

import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd.verify(raw, hashed)


@lru_cache(maxsize=1)
def load_private_key() -> str:
    p: Path = settings.jwt.private_key_path
    return p.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_public_key() -> str:
    p: Path = settings.jwt.public_key_path
    return p.read_text(encoding="utf-8")


def _create_token(
    sub: str,
    *,
    ttl_minutes: int,
    token_type: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(sub),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
        "type": token_type,
    }
    private_key = load_private_key()
    return jwt.encode(payload, private_key, algorithm=settings.jwt.algorithm)


def create_access_token(sub: str) -> str:
    return _create_token(
        sub, ttl_minutes=settings.jwt.access_ttl_min, token_type="access"
    )


def create_refresh_token(sub: str) -> str:
    # тут было бы полезно ввести jti для потверждения токена через бд, но в данном проекте было принято решение не хранить токены и осоответсвующую информацию в бд, поэтому и jti ут нет
    return _create_token(
        sub, ttl_minutes=settings.jwt.refresh_ttl_min, token_type="refresh"
    )


def decode_token(token: str) -> dict:
    public_key = load_public_key()
    return jwt.decode(token, public_key, algorithms=[settings.jwt.algorithm])
