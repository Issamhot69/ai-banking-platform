import pytest

TEST_ACCOUNT_ID = "22222222-3333-4444-5555-666666666666"

class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "sepa_zone" in data

class TestSEPAUtils:
    async def test_get_sepa_countries(self, client, auth_headers):
        response = await client.get("/api/v1/sepa/countries", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sepa_countries" in data
        assert len(data["sepa_countries"]) > 30

    async def test_validate_valid_iban(self, client, auth_headers):
        response = await client.get(
            "/api/v1/sepa/validate/iban/FR7630006000011234567890189",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["valid"] == True

    async def test_validate_invalid_country_iban(self, client, auth_headers):
        response = await client.get(
            "/api/v1/sepa/validate/iban/US12345678901234",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["valid"] == False

class TestSEPATransfer:
    async def test_sct_transfer(self, client, auth_headers):
        response = await client.post("/api/v1/sepa/transfer", json={
            "from_account_id": TEST_ACCOUNT_ID,
            "debtor_name": "Jean Dupont",
            "debtor_iban": "MA860015500107777777777",
            "creditor_name": "Marie Martin",
            "creditor_iban": "FR7630006000011234567890189",
            "creditor_bic": "BNPAFRPP",
            "amount": 250,
            "remittance_info": "Test SCT",
            "is_instant": False,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["transfer_type"] == "SCT"
        assert data["status"] == "completed"
        assert float(data["fee"]) == 0.50

    async def test_sct_instant_transfer(self, client, auth_headers):
        response = await client.post("/api/v1/sepa/transfer", json={
            "from_account_id": TEST_ACCOUNT_ID,
            "debtor_name": "Jean Dupont",
            "debtor_iban": "MA860015500107777777777",
            "creditor_name": "Marie Martin",
            "creditor_iban": "DE89370400440532013000",
            "creditor_bic": "COBADEFFXXX",
            "amount": 100,
            "remittance_info": "Test SCT Inst",
            "is_instant": True,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["transfer_type"] == "SCT Inst"
        assert data["is_instant"] == True
        assert float(data["fee"]) == 1.00

    async def test_get_transfers(self, client, auth_headers):
        response = await client.get("/api/v1/sepa/transfers", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_non_sepa_iban_rejected(self, client, auth_headers):
        response = await client.post("/api/v1/sepa/transfer", json={
            "from_account_id": TEST_ACCOUNT_ID,
            "debtor_name": "Jean Dupont",
            "debtor_iban": "MA860015500107777777777",
            "creditor_name": "John Smith",
            "creditor_iban": "US12345678901234567",
            "amount": 100,
            "is_instant": False,
        }, headers=auth_headers)
        assert response.status_code == 400
