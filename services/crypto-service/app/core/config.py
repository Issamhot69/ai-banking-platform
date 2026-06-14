from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Bank Crypto Wallet Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"

    SUPPORTED_CRYPTOS: list = ["BTC", "ETH", "USDT", "BNB", "SOL", "MAD_COIN"]
    TRANSACTION_FEE_PERCENT: float = 0.5
    MIN_TRANSACTION: float = 10.0

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
