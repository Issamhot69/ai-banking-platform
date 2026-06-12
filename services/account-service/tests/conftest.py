import pytest
import uuid
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text, Column, String
from sqlalchemy.dialects.postgresql import UUID
from jose import jwt

from app.core.database import Base, get_db
from app.main import app
import app.api.accounts as accounts_module
from app.models.account import Account  # noqa: F401 — enregistre le modèle dans Base.metadata

DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = str(uuid.uuid4())


# Modèle minimal "users" pour satisfaire la FK accounts.user_id
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
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("INSERT INTO users (id, email) VALUES (:id, :email) ON CONFLICT (id) DO NOTHING"),
            {"id": TEST_USER_ID, "email": "test@bank.com"}
        )
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))


@pytest.fixture
async def client():
    from httpx import AsyncClient, ASGITransport

    accounts_module.publish_event = AsyncMock(return_value=None)

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
    token = create_test_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_other_user():
    other_id = str(uuid.uuid4())
    token = create_test_token(user_id=other_id, email="other@bank.com")
    return {"Authorization": f"Bearer {token}"}
