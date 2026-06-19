from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Bank Transaction Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    REDIS_URL: str = "redis://:redispass123@redis:6379/2"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"

    MAX_SINGLE_TRANSFER: float = 50000.00
    MAX_DAILY_TRANSFERS: int = 20
    FRAUD_AMOUNT_THRESHOLD: float = 10000.00
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
