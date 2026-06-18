import pytest
import uuid
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text, Column, String, Numeric, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from jose import jwt

from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app
import app.api.transactions as tx_module
from app.models.transaction import Transaction  # noqa: F401
from app.models.standing_order import StandingOrder  # noqa: F401
from app.models.savings_goal import SavingsGoal  # noqa: F401

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = str(uuid.uuid4())
FROM_ACCOUNT_ID = str(uuid.uuid4())
TO_ACCOUNT_ID = str(uuid.uuid4())
OTHER_ACCOUNT_ID = str(uuid.uuid4())
LIMIT_ACCOUNT_ID = str(uuid.uuid4())


# Modèles minimaux pour les FK
class TestUser(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)


class TestAccount(Base):
    __tablename__ = "accounts"
    __table_args__ = {"extend_existing": True}
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    account_number = Column(String(20), unique=True, nullable=False)
    iban = Column(String(34), unique=True, nullable=True)
    account_type = Column(String(20), nullable=False)
    currency = Column(String(3), default="EUR")
    balance = Column(Numeric(15, 2), default=Decimal("0.00"))
    available_balance = Column(Numeric(15, 2), default=Decimal("0.00"))
    status = Column(String(20), default="active")
    is_primary = Column(Boolean, default=False)
    daily_transfer_limit = Column(Numeric(15, 2), default=Decimal("10000.00"))
    monthly_transfer_limit = Column(Numeric(15, 2), default=Decimal("50000.00"))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


# Fake Redis supportant incr/expire/get pour FraudDetector
class FakeRedis:
    def __init__(self):
        self._store = {}

    async def incr(self, key):
        self._store[key] = self._store.get(key, 0) + 1
        return self._store[key]

    async def expire(self, key, ttl):
        return True

    async def get(self, key):
        return self._store.get(key)


_fake_redis = FakeRedis()


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
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("""INSERT INTO users (id, email, password_hash, first_name, last_name,
                is_active, is_verified, kyc_status, is_2fa_enabled, created_at, updated_at)
                VALUES (:id, :email, 'testhash', 'Test', 'Transaction',
                true, true, 'pending', false, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING"""),
            {"id": TEST_USER_ID, "email": "test@bank.com"}
        )
        now = datetime.now(timezone.utc)
        # Compte source — appartient à TEST_USER_ID, solde 5000
        await conn.execute(
            text("""INSERT INTO accounts
                (id, user_id, account_number, iban, account_type, currency, balance, available_balance,
                 status, is_primary, daily_transfer_limit, monthly_transfer_limit, created_at, updated_at)
                VALUES (:id, :uid, :num, :iban, 'checking', 'EUR', 5000.00, 5000.00,
                        'active', true, 10000.00, 50000.00, :now, :now)
                ON CONFLICT (id) DO NOTHING"""),
            {"id": FROM_ACCOUNT_ID, "uid": TEST_USER_ID, "num": "FR0001", "iban": "MA00FR0001", "now": now}
        )
        # Compte destinataire — autre utilisateur
        other_user_id = str(uuid.uuid4())
        await conn.execute(
            text("""INSERT INTO users (id, email, password_hash, first_name, last_name,
                is_active, is_verified, kyc_status, is_2fa_enabled, created_at, updated_at)
                VALUES (:id, :email, 'testhash', 'Dest', 'User',
                true, true, 'pending', false, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING"""),
            {"id": other_user_id, "email": "dest@bank.com"}
        )
        await conn.execute(
            text("""INSERT INTO accounts
                (id, user_id, account_number, iban, account_type, currency, balance, available_balance,
                 status, is_primary, daily_transfer_limit, monthly_transfer_limit, created_at, updated_at)
                VALUES (:id, :uid, :num, :iban, 'checking', 'EUR', 1000.00, 1000.00,
                        'active', false, 10000.00, 50000.00, :now, :now)
                ON CONFLICT (id) DO NOTHING"""),
            {"id": TO_ACCOUNT_ID, "uid": other_user_id, "num": "FR0002", "iban": "MA00FR0002", "now": now}
        )
        # Compte gelé — pour tester rejets
        await conn.execute(
            text("""INSERT INTO accounts
                (id, user_id, account_number, iban, account_type, currency, balance, available_balance,
                 status, is_primary, daily_transfer_limit, monthly_transfer_limit, created_at, updated_at)
                VALUES (:id, :uid, :num, :iban, 'checking', 'EUR', 100.00, 100.00,
                        'frozen', false, 10000.00, 50000.00, :now, :now)
                ON CONFLICT (id) DO NOTHING"""),
            {"id": OTHER_ACCOUNT_ID, "uid": TEST_USER_ID, "num": "FR0003", "iban": "MA00FR0003", "now": now}
        )
        # Compte avec grosse balance mais petite limite journalière
        await conn.execute(
            text("""INSERT INTO accounts
                (id, user_id, account_number, iban, account_type, currency, balance, available_balance,
                 status, is_primary, daily_transfer_limit, monthly_transfer_limit, created_at, updated_at)
                VALUES (:id, :uid, :num, :iban, 'checking', 'EUR', 50000.00, 50000.00,
                        'active', false, 100.00, 50000.00, :now, :now)
                ON CONFLICT (id) DO NOTHING"""),
            {"id": LIMIT_ACCOUNT_ID, "uid": TEST_USER_ID, "num": "FR0004", "iban": "MA00FR0004", "now": now}
        )
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))


@pytest.fixture
async def client():
    from httpx import AsyncClient, ASGITransport

    tx_module.publish_event = AsyncMock(return_value=None)

    async def override_db():
        async with TestSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_redis():
        return _fake_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

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
def account_ids():
    return {
        "from": FROM_ACCOUNT_ID,
        "to": TO_ACCOUNT_ID,
        "frozen": OTHER_ACCOUNT_ID,
        "limit": LIMIT_ACCOUNT_ID,
    }
