from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Bank Security Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    REDIS_URL: str = "redis://:redispass123@redis:6379/5"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_TRANSFER_PER_MINUTE: int = 10

    # IP Blocking
    MAX_FAILED_ATTEMPTS: int = 5
    BLOCK_DURATION_MINUTES: int = 30

    # Whitelist IPs (toujours autorisées)
    WHITELISTED_IPS: List[str] = ["127.0.0.1", "::1"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
