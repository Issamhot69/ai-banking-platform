import pytest
from decimal import Decimal


@pytest.mark.asyncio
class TestSavingsGoals:
    async def test_create_savings_goal(self, client, auth_headers, account_ids):
        response = await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["limit"],
            "name": "Vacances",
            "target_amount": 1000,
            "round_up_enabled": True,
            "round_up_multiple": 1.00,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"
        assert data["current_amount"] == "0.00"

    async def test_create_same_source_and_goal_fails(self, client, auth_headers, account_ids):
        response = await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["from"],
            "name": "Invalide",
        })
        assert response.status_code == 400

    async def test_invalid_round_up_multiple(self, client, auth_headers, account_ids):
        response = await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["limit"],
            "name": "Invalide",
            "round_up_multiple": 3.00,
        })
        assert response.status_code == 422

    async def test_list_savings_goals(self, client, auth_headers, account_ids):
        await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["limit"],
            "name": "Objectif test",
        })
        response = await client.get("/api/v1/savings-goals", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["savings_goals"]) >= 1

    async def test_pause_and_resume_goal(self, client, auth_headers, account_ids):
        create_resp = await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["limit"],
            "name": "Pause test",
        })
        goal_id = create_resp.json()["id"]

        pause_resp = await client.post(f"/api/v1/savings-goals/{goal_id}/pause", headers=auth_headers)
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "paused"
        assert pause_resp.json()["round_up_enabled"] is False

        resume_resp = await client.post(f"/api/v1/savings-goals/{goal_id}/resume", headers=auth_headers)
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "active"

    async def test_cancel_goal(self, client, auth_headers, account_ids):
        create_resp = await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["limit"],
            "name": "À annuler",
        })
        goal_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/savings-goals/{goal_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
class TestRoundUpIntegration:
    async def test_transfer_triggers_round_up(self, client, auth_headers, account_ids):
        await client.post("/api/v1/savings-goals", headers=auth_headers, json={
            "source_account_id": account_ids["from"],
            "goal_account_id": account_ids["limit"],
            "name": "Test arrondi",
            "round_up_enabled": True,
            "round_up_multiple": 1.00,
        })

        # Virement de 23.40 — devrait déclencher un arrondi de 0.60
        response = await client.post("/api/v1/transactions/transfer", headers=auth_headers, json={
            "from_account_id": account_ids["from"],
            "to_account_id": account_ids["to"],
            "amount": 23.40,
            "currency": "EUR",
        })
        assert response.status_code == 201

        goals_resp = await client.get("/api/v1/savings-goals", headers=auth_headers)
        goal = goals_resp.json()["savings_goals"][0]
        assert Decimal(goal["current_amount"]) == Decimal("0.60")
        assert goal["contribution_count"] == 1
