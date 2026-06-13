from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Bank SEPA Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"

    BANK_BIC: str = "AIBKMAMC"
    BANK_NAME: str = "AI Banking Platform"

    SEPA_FEE_STANDARD: float = 0.50
    SEPA_FEE_INSTANT: float = 1.00
    SEPA_MAX_AMOUNT_INSTANT: float = 100000.00

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
