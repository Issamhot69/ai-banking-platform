import pytest


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestCreateAccount:
    @pytest.mark.asyncio
    async def test_create_account_success(self, client, auth_headers):
        response = await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "EUR"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "checking"
        assert data["currency"] == "EUR"
        assert data["balance"] == "0.00"
        assert data["iban"] is not None
        assert data["account_number"] is not None

    @pytest.mark.asyncio
    async def test_create_account_invalid_type(self, client, auth_headers):
        response = await client.post(
            "/api/v1/accounts",
            json={"account_type": "invalid_type", "currency": "EUR"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_account_invalid_currency(self, client, auth_headers):
        response = await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "XXX"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_account_without_token(self, client):
        response = await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "EUR"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_account_savings(self, client, auth_headers):
        response = await client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "USD"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["account_type"] == "savings"
        assert response.json()["currency"] == "USD"


class TestGetAccounts:
    @pytest.mark.asyncio
    async def test_get_my_accounts(self, client, auth_headers):
        # Créer un compte d'abord
        await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "EUR"},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total_accounts" in data
        assert "total_balance" in data
        assert data["total_accounts"] >= 1

    @pytest.mark.asyncio
    async def test_get_accounts_without_token(self, client):
        response = await client.get("/api/v1/accounts")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_account_by_id(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/accounts",
            json={"account_type": "business", "currency": "MAD"},
            headers=auth_headers,
        )
        account_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == account_id

    @pytest.mark.asyncio
    async def test_get_account_other_user_forbidden(self, client, auth_headers, auth_headers_other_user):
        create_resp = await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "EUR"},
            headers=auth_headers,
        )
        account_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers_other_user)
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(self, client, auth_headers):
        import uuid
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/accounts/{fake_id}", headers=auth_headers)
        assert response.status_code == 404


class TestFreezeAccount:
    @pytest.mark.asyncio
    async def test_freeze_account(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "EUR"},
            headers=auth_headers,
        )
        account_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/accounts/{account_id}/freeze",
            json={"reason": "Suspicious activity"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        get_resp = await client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers)
        assert get_resp.json()["status"] == "frozen"


class TestUpdateLimits:
    @pytest.mark.asyncio
    async def test_update_limits(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/accounts",
            json={"account_type": "checking", "currency": "EUR"},
            headers=auth_headers,
        )
        account_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/accounts/{account_id}/limits",
            json={"daily_transfer_limit": 5000, "monthly_transfer_limit": 20000},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Limites mises à jour"

        get_resp = await client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers)
        data = get_resp.json()
        assert data["daily_transfer_limit"] == "5000.00"
        assert data["monthly_transfer_limit"] == "20000.00"
