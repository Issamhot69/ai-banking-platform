import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
class TestStandingOrders:
    async def test_create_standing_order_success(self, client, auth_headers, account_ids):
        response = await client.post("/api/v1/standing-orders", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 100,
            "currency": "EUR",
            "frequency": "monthly",
            "description": "Loyer",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"
        assert data["frequency"] == "monthly"
        assert data["execution_count"] == 0

    async def test_create_invalid_frequency(self, client, auth_headers, account_ids):
        response = await client.post("/api/v1/standing-orders", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 100,
            "frequency": "yearly",
        })
        assert response.status_code == 422

    async def test_create_unauthorized(self, client, account_ids):
        response = await client.post("/api/v1/standing-orders", json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 100,
            "frequency": "daily",
        })
        assert response.status_code == 401

    async def test_list_standing_orders(self, client, auth_headers, account_ids):
        await client.post("/api/v1/standing-orders", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 25,
            "frequency": "weekly",
        })
        response = await client.get("/api/v1/standing-orders", headers=auth_headers)
        assert response.status_code == 200
        orders = response.json()["standing_orders"]
        assert len(orders) >= 1

    async def test_cancel_standing_order(self, client, auth_headers, account_ids):
        create_resp = await client.post("/api/v1/standing-orders", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 50,
            "frequency": "daily",
        })
        order_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/standing-orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    async def test_pause_and_resume(self, client, auth_headers, account_ids):
        create_resp = await client.post("/api/v1/standing-orders", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 50,
            "frequency": "daily",
        })
        order_id = create_resp.json()["id"]

        pause_resp = await client.post(f"/api/v1/standing-orders/{order_id}/pause", headers=auth_headers)
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "paused"

        pause_again = await client.post(f"/api/v1/standing-orders/{order_id}/pause", headers=auth_headers)
        assert pause_again.status_code == 400

        resume_resp = await client.post(f"/api/v1/standing-orders/{order_id}/resume", headers=auth_headers)
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "active"

    async def test_cancel_nonexistent_order(self, client, auth_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/api/v1/standing-orders/{fake_id}", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestStandingOrderExecution:
    async def test_execute_due_standing_order_moves_balance(self, client, auth_headers, account_ids):
        from app.tasks.standing_orders import execute_due_standing_orders

        create_resp = await client.post("/api/v1/standing-orders", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 75,
            "frequency": "daily",
        })
        order_id = create_resp.json()["id"]
        initial_next_date = create_resp.json()["next_execution_date"]

        executed_count = await execute_due_standing_orders()
        assert executed_count >= 1

        list_resp = await client.get("/api/v1/standing-orders", headers=auth_headers)
        orders = {o["id"]: o for o in list_resp.json()["standing_orders"]}
        order = orders[order_id]
        assert order["execution_count"] == 1
        assert order["last_executed_at"] is not None
        assert order["next_execution_date"] != initial_next_date
