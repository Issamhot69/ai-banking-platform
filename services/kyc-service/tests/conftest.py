import pytest
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["ANTHROPIC_API_KEY"] = "test_key"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from jose import jwt

from app.core.database import Base, get_db
from app.main import app

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_EMAIL = "kyc_unique_test_9999@bank.com"

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
        await conn.execute(
            text("DELETE FROM kyc_applications WHERE user_id = :id"),
            {"id": TEST_USER_ID}
        )
        await conn.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": TEST_EMAIL}
        )
        await conn.execute(
            text("INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, kyc_status, is_2fa_enabled, created_at, updated_at) VALUES (:id, :email, 'testhash', 'Test', 'KYC', true, true, 'pending', false, NOW(), NOW())"),
            {"id": TEST_USER_ID, "email": TEST_EMAIL}
        )
    yield

@pytest.fixture
async def client():
    from httpx import AsyncClient, ASGITransport

    async def override_db():
        async with TestSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_test_token()}"}
