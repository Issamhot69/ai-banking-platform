import pytest
from decimal import Decimal


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestTransfer:
    @pytest.mark.asyncio
    async def test_transfer_success(self, client, auth_headers, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 100.00,
                "currency": "EUR",
                "description": "Test transfer",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "transfer"
        assert data["amount"] == "100.00"
        assert data["status"] == "completed"
        assert data["reference"].startswith("TRF")
        assert Decimal(data["balance_before"]) - Decimal(data["balance_after"]) == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_transfer_insufficient_balance(self, client, auth_headers, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 999999.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        # 999999 > max 50000 -> validation error 422, sinon 400 solde insuffisant
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_transfer_exceeds_daily_limit(self, client, auth_headers, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["limit"],
                "to_account_id": account_ids["to"],
                "amount": 200.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "limite" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_transfer_negative_amount(self, client, auth_headers, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": -50.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transfer_invalid_currency(self, client, auth_headers, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 50.00,
                "currency": "XXX",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transfer_from_frozen_account(self, client, auth_headers, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["frozen"],
                "to_account_id": account_ids["to"],
                "amount": 10.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_transfer_to_nonexistent_account(self, client, auth_headers, account_ids):
        import uuid
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": str(uuid.uuid4()),
                "amount": 10.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_transfer_without_token(self, client, account_ids):
        response = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 10.00,
                "currency": "EUR",
            },
        )
        assert response.status_code == 401


class TestGetTransactions:
    @pytest.mark.asyncio
    async def test_get_transactions_list(self, client, auth_headers, account_ids):
        # Créer une transaction
        await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 50.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        response = await client.get(
            "/api/v1/transactions",
            params={"account_id": account_ids["from"], "page": 1, "per_page": 20},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_transaction_by_id(self, client, auth_headers, account_ids):
        create_resp = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 25.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        tx_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/transactions/{tx_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == tx_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_transaction(self, client, auth_headers):
        import uuid
        response = await client.get(f"/api/v1/transactions/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404


class TestReverseTransaction:
    @pytest.mark.asyncio
    async def test_reverse_transaction(self, client, auth_headers, account_ids):
        create_resp = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 15.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        tx_id = create_resp.json()["id"]

        response = await client.post(f"/api/v1/transactions/{tx_id}/reverse", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Transaction reversée"

    @pytest.mark.asyncio
    async def test_reverse_already_reversed(self, client, auth_headers, account_ids):
        create_resp = await client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": account_ids["from"],
                "to_account_id": account_ids["to"],
                "amount": 5.00,
                "currency": "EUR",
            },
            headers=auth_headers,
        )
        tx_id = create_resp.json()["id"]
        await client.post(f"/api/v1/transactions/{tx_id}/reverse", headers=auth_headers)

        response = await client.post(f"/api/v1/transactions/{tx_id}/reverse", headers=auth_headers)
        assert response.status_code == 400
