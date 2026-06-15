import pytest
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql+asyncpg://bankadmin:bankpass123@postgres:5432/bankdb")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from jose import jwt

from app.core.database import Base, get_db
from app.main import app

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = "44444444-5555-6666-7777-888888888888"
TEST_EMAIL = "loan_test_9999@bank.com"
TEST_ACCOUNT_ID = "55555555-6666-7777-8888-999999999999"

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
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            INSERT INTO users (id, email, password_hash, first_name, last_name,
                is_active, is_verified, kyc_status, is_2fa_enabled, created_at, updated_at)
            VALUES (:id, :email, 'testhash', 'Test', 'Loan',
                true, true, 'pending', false, NOW(), NOW())
            ON CONFLICT (email) DO NOTHING
        """), {"id": TEST_USER_ID, "email": TEST_EMAIL})
        await conn.execute(text("""
            INSERT INTO accounts (id, user_id, account_number, iban, account_type,
                currency, balance, available_balance, status, is_primary,
                daily_transfer_limit, monthly_transfer_limit, created_at, updated_at)
            VALUES (:id, :user_id, '6666666666', 'MA860015500106666666666',
                'checking', 'EUR', 10000, 10000, 'active', true, 50000, 200000, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": TEST_ACCOUNT_ID, "user_id": TEST_USER_ID})
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
