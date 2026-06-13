from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Bank KYC Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    MONGODB_URL: str = "mongodb://bankadmin:mongopass123@mongodb:27017/bank_docs"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION_min32chars"
    ALGORITHM: str = "HS256"

    ANTHROPIC_API_KEY: str = ""
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "pdf"]

    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
