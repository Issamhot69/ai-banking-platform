import pytest

TEST_ACCOUNT_ID = "ffffffff-aaaa-bbbb-cccc-dddddddddddd"

class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "supported_currencies" in data

class TestExchangeRates:
    async def test_get_rates(self, client, auth_headers):
        response = await client.get("/api/v1/swift/rates", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    async def test_convert_usd_to_eur(self, client, auth_headers):
        response = await client.get(
            "/api/v1/swift/rates/convert?amount=1000&from_currency=USD&to_currency=EUR",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "EUR"
        assert float(data["converted_amount"]) > 0

    async def test_convert_gbp_to_eur(self, client, auth_headers):
        response = await client.get(
            "/api/v1/swift/rates/convert?amount=500&from_currency=GBP&to_currency=EUR",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert float(response.json()["converted_amount"]) > 0

class TestSWIFTTransfer:
    async def test_create_transfer(self, client, auth_headers):
        response = await client.post("/api/v1/swift/transfer", json={
            "from_account_id": TEST_ACCOUNT_ID,
            "sender_name": "Jean Dupont",
            "sender_country": "MA",
            "beneficiary_name": "John Smith",
            "beneficiary_country": "GB",
            "beneficiary_account": "GB29NWBK60161331926819",
            "beneficiary_bank_name": "Barclays Bank PLC",
            "beneficiary_bic": "BARCGB22",
            "amount": 500,
            "currency": "EUR",
            "remittance_info": "Test transfer",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "completed"
        assert data["beneficiary_bic"] == "BARCGB22"
        assert float(data["fee"]) > 0

    async def test_transfer_aml_blocked(self, client, auth_headers):
        response = await client.post("/api/v1/swift/transfer", json={
            "from_account_id": TEST_ACCOUNT_ID,
            "sender_name": "Jean Dupont",
            "sender_country": "MA",
            "beneficiary_name": "Unknown Person",
            "beneficiary_country": "KP",
            "beneficiary_account": "KP1234567890",
            "beneficiary_bank_name": "Unknown Bank",
            "beneficiary_bic": "UNKNKPXX",
            "amount": 100,
            "currency": "EUR",
        }, headers=auth_headers)
        assert response.status_code == 403

    async def test_get_transfers(self, client, auth_headers):
        response = await client.get("/api/v1/swift/transfers", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_validate_bic(self, client, auth_headers):
        response = await client.get("/api/v1/swift/validate/bic/BARCGB22", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["country_code"] == "GB"

    async def test_invalid_currency(self, client, auth_headers):
        response = await client.post("/api/v1/swift/transfer", json={
            "from_account_id": TEST_ACCOUNT_ID,
            "sender_name": "Test",
            "sender_country": "MA",
            "beneficiary_name": "Test",
            "beneficiary_country": "US",
            "beneficiary_account": "US123456",
            "beneficiary_bank_name": "Test Bank",
            "beneficiary_bic": "TESTUS33",
            "amount": 100,
            "currency": "INVALID",
        }, headers=auth_headers)
        assert response.status_code == 422
