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

TEST_USER_ID = "cccccccc-dddd-eeee-ffff-aaaaaaaaaaaa"
TEST_EMAIL = "card_test_9999@bank.com"
TEST_ACCOUNT_ID = "dddddddd-eeee-ffff-aaaa-bbbbbbbbbbbb"

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
        # -- ROBUST USERS+ACCOUNTS SETUP --
        await conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
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
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS accounts ("
            "id UUID PRIMARY KEY, "
            "user_id UUID NOT NULL, "
            "account_number VARCHAR(20) UNIQUE NOT NULL, "
            "iban VARCHAR(34), "
            "account_type VARCHAR(20) NOT NULL, "
            "currency VARCHAR(3) NOT NULL, "
            "balance NUMERIC(15,2) NOT NULL DEFAULT 0, "
            "available_balance NUMERIC(15,2) NOT NULL DEFAULT 0, "
            "status VARCHAR(20) NOT NULL DEFAULT 'active', "
            "is_primary BOOLEAN NOT NULL DEFAULT false, "
            "daily_transfer_limit NUMERIC(15,2) NOT NULL DEFAULT 10000, "
            "monthly_transfer_limit NUMERIC(15,2) NOT NULL DEFAULT 50000, "
            "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), "
            "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())"
        ))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                date_of_birth DATE,
                national_id VARCHAR(50),
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                kyc_status VARCHAR(20) DEFAULT 'pending',
                totp_secret VARCHAR(255),
                is_2fa_enabled BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS accounts (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                account_number VARCHAR(20) UNIQUE NOT NULL,
                iban VARCHAR(34),
                account_type VARCHAR(20) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                balance NUMERIC(15,2) NOT NULL,
                available_balance NUMERIC(15,2) NOT NULL,
                status VARCHAR(20) NOT NULL,
                is_primary BOOLEAN NOT NULL DEFAULT false,
                daily_transfer_limit NUMERIC(15,2) NOT NULL,
                monthly_transfer_limit NUMERIC(15,2) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            INSERT INTO users (id, email, password_hash, first_name, last_name,
                is_active, is_verified, kyc_status, is_2fa_enabled, created_at, updated_at)
            VALUES (:id, :email, 'testhash', 'Test', 'Card',
                true, true, 'pending', false, NOW(), NOW())
            ON CONFLICT (email) DO NOTHING
        """), {"id": TEST_USER_ID, "email": TEST_EMAIL})
        await conn.execute(text("""
            INSERT INTO accounts (id, user_id, account_number, iban, account_type,
                currency, balance, available_balance, status, is_primary,
                daily_transfer_limit, monthly_transfer_limit, created_at, updated_at)
            VALUES (:id, :user_id, '9999999999', 'MA860015500109999999999',
                'checking', 'EUR', 5000, 5000, 'active', true, 10000, 50000, NOW(), NOW())
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
