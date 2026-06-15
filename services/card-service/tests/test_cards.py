import pytest

TEST_ACCOUNT_ID = "dddddddd-eeee-ffff-aaaa-bbbbbbbbbbbb"

class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestCards:
    async def test_create_visa_card(self, client, auth_headers):
        response = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Jean Dupont",
            "card_type": "visa",
            "daily_limit": 500,
            "monthly_limit": 2000,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["card_type"] == "visa"
        assert data["status"] == "active"
        assert "card_number" in data
        assert "cvv" in data
        assert data["card_holder_name"] == "JEAN DUPONT"

    async def test_create_mastercard(self, client, auth_headers):
        response = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Jean Dupont",
            "card_type": "mastercard",
            "daily_limit": 1000,
            "monthly_limit": 5000,
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["card_type"] == "mastercard"

    async def test_get_my_cards(self, client, auth_headers):
        response = await client.get("/api/v1/cards", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    async def test_get_card_by_id(self, client, auth_headers):
        create_res = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Test User",
            "card_type": "visa",
        }, headers=auth_headers)
        card_id = create_res.json()["id"]
        response = await client.get(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == card_id

    async def test_freeze_card(self, client, auth_headers):
        create_res = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Test Freeze",
            "card_type": "visa",
        }, headers=auth_headers)
        card_id = create_res.json()["id"]
        response = await client.post(f"/api/v1/cards/{card_id}/freeze", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "frozen"

    async def test_unfreeze_card(self, client, auth_headers):
        create_res = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Test Unfreeze",
            "card_type": "visa",
        }, headers=auth_headers)
        card_id = create_res.json()["id"]
        await client.post(f"/api/v1/cards/{card_id}/freeze", headers=auth_headers)
        response = await client.post(f"/api/v1/cards/{card_id}/unfreeze", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    async def test_update_card_limits(self, client, auth_headers):
        create_res = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Test Update",
            "card_type": "visa",
        }, headers=auth_headers)
        card_id = create_res.json()["id"]
        response = await client.patch(f"/api/v1/cards/{card_id}", json={
            "daily_limit": 2000,
            "monthly_limit": 10000,
        }, headers=auth_headers)
        assert response.status_code == 200
        assert float(response.json()["daily_limit"]) == 2000

    async def test_cancel_card(self, client, auth_headers):
        create_res = await client.post("/api/v1/cards", json={
            "account_id": TEST_ACCOUNT_ID,
            "card_holder_name": "Test Cancel",
            "card_type": "visa",
        }, headers=auth_headers)
        card_id = create_res.json()["id"]
        response = await client.delete(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert response.status_code == 200

    async def test_unauthorized_access(self, client):
        response = await client.get("/api/v1/cards")
        assert response.status_code == 403
