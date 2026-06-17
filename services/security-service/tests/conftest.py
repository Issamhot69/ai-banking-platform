import pytest
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["REDIS_URL"] = "redis://localhost:6379/5"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from jose import jwt

from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = "33333333-4444-5555-6666-777777777777"
TEST_EMAIL = "security_test_9999@bank.com"

def create_test_token():
    payload = {
        "sub": TEST_USER_ID,
        "email": TEST_EMAIL,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, os.environ["SECRET_KEY"], algorithm="HS256")

@pytest.fixture(autouse=True, scope="session")
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS users ("
            "id UUID PRIMARY KEY, "
            "email VARCHAR(255) UNIQUE NOT NULL, "
            "phone VARCHAR(20), "
            "password_hash VARCHAR(255) NOT NULL, "
            "first_name VARCHAR(100), "
            "last_name VARCHAR(100), "
            "date_of_birth DATE, "
            "national_id VARCHAR(50), "
            "is_active BOOLEAN DEFAULT true, "
            "is_verified BOOLEAN DEFAULT false, "
            "kyc_status VARCHAR(20) DEFAULT 'pending', "
            "totp_secret VARCHAR(255), "
            "is_2fa_enabled BOOLEAN DEFAULT false, "
            "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), "
            "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())"
        ))
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.fixture
def mock_redis():
    import fakeredis.aioredis as fakeredis
    return fakeredis.FakeRedis()

@pytest.fixture
async def client(mock_redis):
    from httpx import AsyncClient, ASGITransport

    async def override_db():
        async with TestSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_test_token()}"}
