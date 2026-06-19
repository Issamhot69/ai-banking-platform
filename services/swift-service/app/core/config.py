from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Bank SWIFT Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"

    BANK_BIC: str = "AIBKMAMC"
    BANK_NAME: str = "AI Banking Platform"
    BANK_COUNTRY: str = "MA"

    SWIFT_FEE_PERCENTAGE: float = 0.5
    SWIFT_MIN_FEE: float = 15.0
    SWIFT_MAX_FEE: float = 50.0
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
