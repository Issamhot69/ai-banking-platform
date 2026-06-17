import pytest
import uuid
import os

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

_stored_tokens = {}

class SmartMockRedis:
    async def setex(self, key, ttl, value):
        _stored_tokens[key] = value
        return True
    async def get(self, key):
        return _stored_tokens.get(key)
    async def delete(self, key):
        _stored_tokens.pop(key, None)
        return True

_mock_redis = SmartMockRedis()

import app.core.redis as redis_module
redis_module.redis_client = _mock_redis

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


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
    # Drop avec CASCADE
    async with test_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                __import__('sqlalchemy').text(
                    "DROP TABLE IF EXISTS notifications, cards, transactions, accounts, users CASCADE"
                )
            )
        )


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

    async def override_redis():
        return _mock_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    unique = str(uuid.uuid4()).replace("-", "")[:8]
    return {
        "email": f"test_{unique}@bank.com",
        "password": "Test@1234",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
async def registered_user(client, test_user_data):
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201, f"Register failed: {response.text}"
    return test_user_data


@pytest.fixture
async def logged_in_user(client, registered_user):
    response = await client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return {**registered_user, **response.json()}


@pytest.fixture
async def auth_headers(logged_in_user):
    return {"Authorization": f"Bearer {logged_in_user['access_token']}"}
