from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Bank Notification Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    MONGODB_URL: str = "mongodb://bankadmin:mongopass123@mongodb:27017/bank_docs"
    REDIS_URL: str = "redis://:redispass123@redis:6379/4"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"

    FIREBASE_CREDENTIALS_PATH: str = "/app/firebase-credentials.json"
    SENDGRID_API_KEY: str = "your_sendgrid_api_key"
    FROM_EMAIL: str = "noreply@aibanking.com"
    FROM_NAME: str = "AI Banking Platform"
    TWILIO_ACCOUNT_SID: str = "your_twilio_sid"
    TWILIO_AUTH_TOKEN: str = "your_twilio_token"
    TWILIO_FROM_NUMBER: str = "+1234567890"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
