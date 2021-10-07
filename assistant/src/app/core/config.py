import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, HttpUrl, PostgresDsn, validator

__all__ = ["settings"]


class Settings(BaseSettings):
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator("SENTRY_DSN", pre=True)
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
        if len(v) == 0:
            return None
        return v

    DEBUG: Optional[bool] = False

    @validator("DEBUG", pre=True)
    def parse_debug(cls, v: str) -> bool:
        if len(v) == 0:
            return False
        if v.lower().strip() in ("false", "0"):
            return False
        if v.lower().strip() in ("true", "1"):
            return True
        return False

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_NAME: str

    @validator("TELEGRAM_BOT_NAME", pre=True)
    def validate_telegram_bot_name(cls, v: str) -> str:
        if v[0] == "@":
            return v[1:]
        return v

    TELEGRAM_BOT_WORKERS: Optional[int]

    @validator("TELEGRAM_BOT_WORKERS", pre=True)
    def validate_telegram_bot_workers(cls, v: Any) -> int:
        if v:
            return int(v)
        return 1

    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            path=f"/{values.get('POSTGRES_DB')}",
        )

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    CELERY_BROKER_URL: Optional[str] = None

    @validator("CELERY_BROKER_URL", pre=True)
    def assemble_celery_broker(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return "redis://{}:{}/{}".format(
            values.get("REDIS_HOST"),
            values.get("REDIS_PORT"),
            values.get("REDIS_DB"),
        )

    CELERY_WORKERS: Optional[int]

    @validator("CELERY_WORKERS", pre=True)
    def validate_celery_workers(cls, v: Any) -> int:
        if v:
            return int(v)
        return 1

    class Config:
        case_sensitive = True


settings = Settings()
