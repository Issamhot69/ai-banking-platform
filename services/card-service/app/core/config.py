from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Bank Card Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"
    ENCRYPTION_KEY: str = "dGhpcytpcythKzMyK2J5dGUrZW5jcnlwdGlvbg=="
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
