from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Bank Auth Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    REDIS_URL: str = "redis://:redispass123@redis:6379/0"

    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    OTP_ISSUER: str = "AI Banking Platform"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
