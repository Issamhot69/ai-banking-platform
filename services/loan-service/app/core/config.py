from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Bank Loan Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"

    # Paramètres de prêt
    MIN_LOAN_AMOUNT: float = 1000.0
    MAX_LOAN_AMOUNT: float = 100000.0
    MIN_LOAN_TERM_MONTHS: int = 6
    MAX_LOAN_TERM_MONTHS: int = 84
    BASE_INTEREST_RATE: float = 5.0

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
