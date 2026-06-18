import pytest
import uuid
import os
from datetime import datetime, timedelta, timezone

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text, Column, String
from sqlalchemy.dialects.postgresql import UUID
from jose import jwt

from app.core.database import Base, get_db
from app.main import app
from app.models.notification import Notification  # noqa: F401

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = str(uuid.uuid4())


class TestUser(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)


def create_test_token(user_id: str = TEST_USER_ID, email: str = "test@bank.com"):
    payload = {
        "sub": user_id,
        "email": email,
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
        await conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
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
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, kyc_status, is_2fa_enabled, created_at, updated_at) VALUES (:id, :email, 'testhash', 'Test', 'Notification', true, true, 'pending', false, NOW(), NOW()) ON CONFLICT (id) DO NOTHING"),
            {"id": TEST_USER_ID, "email": "test@bank.com"}
        )
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM notifications WHERE 1=1"))
        await conn.execute(text("DELETE FROM users WHERE 1=1"))


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

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_test_token()}"}


@pytest.fixture
def test_user_id():
    return TEST_USER_ID
