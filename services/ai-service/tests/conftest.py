import pytest
import uuid
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ["ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["ANTHROPIC_API_KEY"] = "test_key_not_real"

from jose import jwt
from app.main import app
from app.ml.nlp import chatbot as chatbot_module


def create_test_token(user_id: str = None, email: str = "test@bank.com"):
    user_id = user_id or str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, os.environ["SECRET_KEY"], algorithm="HS256")


@pytest.fixture
async def client():
    from httpx import AsyncClient, ASGITransport

    # Mock le chatbot Claude pour éviter les appels API réels
    chatbot_module.chatbot.chat = AsyncMock(return_value={
        "reply": "Votre solde est de 1500.00 EUR.",
        "intent": "balance_inquiry",
        "model": "claude-sonnet-4-20250514",
        "tokens_used": 42,
    })
    chatbot_module.chatbot.analyze_spending = AsyncMock(return_value={
        "insights": ["Vous dépensez plus en restauration ce mois-ci"],
        "categories": {"food": 450.0, "transport": 120.0},
        "trends": ["Augmentation de 10% par rapport au mois dernier"],
        "tips": ["Essayez de réduire les dépenses en restauration"],
        "health_score": 75,
        "raw_analysis": None,
    })

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_test_token()}"}
