import pytest

TEST_USER_ID = "77777777-8888-9999-aaaa-bbbbbbbbbbbb"

class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "features" in data

class TestCustomerProfiles:
    async def test_create_profile(self, client, auth_headers):
        response = await client.post("/api/v1/crm/customers", json={
            "user_id": TEST_USER_ID,
            "segment": "premium",
            "notes": "Test client",
            "preferred_channel": "app",
        }, headers=auth_headers)
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            assert response.json()["segment"] == "premium"

    async def test_get_all_customers(self, client, auth_headers):
        response = await client.get("/api/v1/crm/customers", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_customer_by_user_id(self, client, auth_headers):
        await client.post("/api/v1/crm/customers", json={
            "user_id": TEST_USER_ID,
            "segment": "standard",
        }, headers=auth_headers)
        response = await client.get(f"/api/v1/crm/customers/{TEST_USER_ID}", headers=auth_headers)
        assert response.status_code == 200

    async def test_update_customer(self, client, auth_headers):
        response = await client.patch(f"/api/v1/crm/customers/{TEST_USER_ID}", json={
            "is_vip": True,
            "satisfaction_score": 4.5,
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["is_vip"] == True

    async def test_get_crm_stats(self, client, auth_headers):
        response = await client.get("/api/v1/crm/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "vip_customers" in data

class TestTickets:
    async def test_create_ticket(self, client, auth_headers):
        response = await client.post("/api/v1/crm/tickets", json={
            "subject": "Test ticket",
            "description": "Test description",
            "category": "payment",
            "priority": "high",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == "Test ticket"
        assert data["status"] == "open"
        assert data["ticket_number"].startswith("TKT-")

    async def test_get_tickets(self, client, auth_headers):
        response = await client.get("/api/v1/crm/tickets", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_resolve_ticket(self, client, auth_headers):
        create_res = await client.post("/api/v1/crm/tickets", json={
            "subject": "To resolve",
            "description": "Test",
            "category": "support",
            "priority": "low",
        }, headers=auth_headers)
        ticket_id = create_res.json()["id"]
        response = await client.patch(f"/api/v1/crm/tickets/{ticket_id}", json={
            "status": "resolved",
            "resolution": "Issue fixed",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

class TestInteractions:
    async def test_add_interaction(self, client, auth_headers):
        response = await client.post(f"/api/v1/crm/customers/{TEST_USER_ID}/interactions", json={
            "interaction_type": "call",
            "channel": "phone",
            "summary": "Client called about transfer",
            "agent": "Agent Smith",
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["interaction_type"] == "call"

    async def test_get_interactions(self, client, auth_headers):
        response = await client.get(f"/api/v1/crm/customers/{TEST_USER_ID}/interactions", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
