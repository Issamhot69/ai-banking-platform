from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Bank AI Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb"
    REDIS_URL: str = "redis://:redispass123@redis:6379/3"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    SECRET_KEY: str = "supersecretkey_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"

    ANTHROPIC_API_KEY: str = "your_anthropic_api_key_here"
    FRAUD_MODEL_PATH: str = "/app/models/fraud_model.pkl"
    SCORING_MODEL_PATH: str = "/app/models/scoring_model.pkl"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
