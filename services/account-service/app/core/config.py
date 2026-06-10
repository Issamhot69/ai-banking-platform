from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Bank Account Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    REDIS_URL: str = "redis://:redispass123@redis:6379/1"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    ENCRYPTION_KEY: str = "dGhpcytpcythKzMyK2J5dGUrZW5jcnlwdGlvbg=="

    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
