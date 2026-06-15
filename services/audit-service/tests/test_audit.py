import pytest


class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuditLogs:
    async def test_create_log(self, client):
        response = await client.post("/api/v1/audit/logs", json={
            "user_id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
            "user_email": "audit_test_9999@bank.com",
            "action": "user_login",
            "resource": "auth",
            "status": "success",
            "service": "auth-service",
            "severity": "info",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["action"] == "user_login"
        assert data["service"] == "auth-service"

    async def test_get_logs(self, client, auth_headers):
        response = await client.get("/api/v1/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_logs_filter_by_service(self, client, auth_headers):
        response = await client.get("/api/v1/audit/logs?service=auth-service", headers=auth_headers)
        assert response.status_code == 200

    async def test_get_logs_filter_by_status(self, client, auth_headers):
        response = await client.get("/api/v1/audit/logs?status=success", headers=auth_headers)
        assert response.status_code == 200

    async def test_create_error_log(self, client):
        response = await client.post("/api/v1/audit/logs", json={
            "action": "transfer_failed",
            "resource": "transaction",
            "status": "error",
            "service": "transaction-service",
            "severity": "high",
            "error_message": "Insufficient funds",
        })
        assert response.status_code == 201
        assert response.json()["status"] == "error"

    async def test_get_single_log(self, client, auth_headers):
        create_response = await client.post("/api/v1/audit/logs", json={
            "action": "card_created",
            "resource": "card",
            "status": "success",
            "service": "card-service",
            "severity": "info",
        })
        log_id = create_response.json()["id"]
        response = await client.get(f"/api/v1/audit/logs/{log_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == log_id

    async def test_get_stats(self, client, auth_headers):
        response = await client.get("/api/v1/audit/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data
        assert "success_count" in data
        assert "error_count" in data

    async def test_export_csv(self, client, auth_headers):
        response = await client.get("/api/v1/audit/export/csv", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
