import pytest


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "models" in data


class TestFraudCheck:
    @pytest.mark.asyncio
    async def test_fraud_check_normal_transaction(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/fraud/check",
            json={
                "account_id": "acc-123",
                "amount": 100.00,
                "transaction_type": "transfer",
                "daily_count": 1,
                "velocity_10min": 1,
                "avg_amount": 100.0,
                "balance_ratio": 0.1,
                "is_international": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_fraud" in data
        assert "risk_score" in data
        assert "flags" in data
        assert "model_used" in data

    @pytest.mark.asyncio
    async def test_fraud_check_high_amount_flagged(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/fraud/check",
            json={
                "account_id": "acc-123",
                "amount": 45000.00,
                "transaction_type": "transfer",
                "daily_count": 8,
                "velocity_10min": 6,
                "avg_amount": 50.0,
                "balance_ratio": 0.95,
                "is_international": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] > 0
        assert len(data["flags"]) > 0

    @pytest.mark.asyncio
    async def test_fraud_check_without_token(self, client):
        response = await client.post(
            "/api/v1/ai/fraud/check",
            json={"account_id": "acc-123", "amount": 100.00},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_fraud_check_missing_fields(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/fraud/check",
            json={"amount": 100.00},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestCreditScore:
    @pytest.mark.asyncio
    async def test_credit_score_good_profile(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/credit-score",
            json={
                "user_id": "user-123",
                "monthly_income": 5000,
                "payment_history_score": 0.95,
                "credit_utilization": 0.15,
                "months_account_open": 36,
                "recent_inquiries": 0,
                "credit_mix_score": 0.8,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert 300 <= data["score"] <= 850
        assert "label" in data
        assert "grade" in data
        assert "interest_rate" in data
        assert "max_loan_amount" in data
        assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    async def test_credit_score_poor_profile(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/credit-score",
            json={
                "user_id": "user-456",
                "monthly_income": 800,
                "payment_history_score": 0.3,
                "credit_utilization": 0.9,
                "months_account_open": 2,
                "recent_inquiries": 5,
                "credit_mix_score": 0.1,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert 300 <= data["score"] <= 850

    @pytest.mark.asyncio
    async def test_credit_score_defaults(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/credit-score",
            json={"user_id": "user-789", "monthly_income": 3000},
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_credit_score_without_token(self, client):
        response = await client.post(
            "/api/v1/ai/credit-score",
            json={"user_id": "user-123", "monthly_income": 3000},
        )
        assert response.status_code == 403


class TestRecommendations:
    @pytest.mark.asyncio
    async def test_get_recommendations(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/recommendations",
            json={
                "user_id": "user-123",
                "avg_balance": 5000.0,
                "monthly_income": 4000.0,
                "monthly_spend": 2500.0,
                "credit_score": 720,
                "has_savings_account": False,
                "top_spending_categories": ["food", "transport"],
                "age": 28,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    async def test_recommendations_defaults(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/recommendations",
            json={"user_id": "user-123"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recommendations_without_token(self, client):
        response = await client.post(
            "/api/v1/ai/recommendations",
            json={"user_id": "user-123"},
        )
        assert response.status_code == 403


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_basic_message(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Quel est mon solde ?",
                "conversation_history": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "intent" in data
        assert "model" in data
        assert "tokens_used" in data

    @pytest.mark.asyncio
    async def test_chat_with_history(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Et mes dépenses ce mois ?",
                "conversation_history": [
                    {"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"},
                ],
                "user_context": {"user_id": "user-123", "balance": 1500.00},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_without_token(self, client):
        response = await client.post(
            "/api/v1/ai/chat",
            json={"message": "test", "conversation_history": []},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/chat",
            json={"message": "", "conversation_history": []},
            headers=auth_headers,
        )
        assert response.status_code in (200, 422)


class TestSpendingAnalysis:
    @pytest.mark.asyncio
    async def test_spending_analysis(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/spending-analysis",
            json={
                "user_id": "user-123",
                "transactions": [
                    {"amount": 50.0, "category": "food", "date": "2026-06-01"},
                    {"amount": 30.0, "category": "transport", "date": "2026-06-02"},
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data or "categories" in data

    @pytest.mark.asyncio
    async def test_spending_analysis_empty_transactions(self, client, auth_headers):
        response = await client.post(
            "/api/v1/ai/spending-analysis",
            json={"user_id": "user-123", "transactions": []},
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_spending_analysis_without_token(self, client):
        response = await client.post(
            "/api/v1/ai/spending-analysis",
            json={"user_id": "user-123", "transactions": []},
        )
        assert response.status_code == 403


class TestAIStatus:
    @pytest.mark.asyncio
    async def test_ai_status(self, client, auth_headers):
        response = await client.get("/api/v1/ai/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "chatbot" in data
        assert "fraud_model" in data
