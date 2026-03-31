class Settings:
    API_URL: str = "http://127.0.0.1:8000"
    ENV: str = "local"
    MODEL_VERSION: str = "2.0"
    REQUEST_TIMEOUT: int = 10
from functools import lru_cache
from typing import Optional, List

try:
    from pydantic_settings import SettingsConfigDict
except Exception:
    SettingsConfigDict = None

# pydantic v2 moved BaseSettings to pydantic-settings package. Support both.
try:
    # pydantic v1 or compatible
    from pydantic import BaseSettings, AnyUrl, Field
except Exception:
    # pydantic v2: use pydantic_settings for BaseSettings
    from pydantic import AnyUrl, Field
    from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment.

    Keep secrets in environment variables or a secrets manager; do not
    commit them to source control. Use `.env` in development only.
    """

    ENV: str = Field("development", env="ENV")
    DEBUG: bool = Field(False, env="DEBUG")

    # Database
    DATABASE_URL: str = Field("sqlite+pysqlite:///:memory:", env="DATABASE_URL")
    DB_ECHO: bool = Field(False, env="DB_ECHO")
    DB_POOL_SIZE: int = Field(10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(20, env="DB_MAX_OVERFLOW")

    # Cache / realtime
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # Security
    SECRET_KEY: str = Field("dev-secret", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 1 day
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"], env="ALLOWED_ORIGINS")

    # Optional monitoring / Sentry
    SENTRY_DSN: Optional[str] = None

    # App metadata
    APP_NAME: str = "CKD-CI"

    # Observability
    REQUEST_TIMEOUT_SECONDS: int = Field(10, env="REQUEST_TIMEOUT_SECONDS")
    REQUEST_MAX_SIZE_MB: int = Field(5, env="REQUEST_MAX_SIZE_MB")

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
