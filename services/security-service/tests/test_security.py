import pytest


class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "features" in data


class TestSecurityEvents:
    async def test_create_event(self, client, auth_headers):
        response = await client.post(
            "/api/v1/security/events?event_type=brute_force&description=Test event&severity=high&ip_address=192.168.1.1"
        )
        assert response.status_code == 201
        data = response.json()
        assert data["event_type"] == "brute_force"
        assert data["severity"] == "high"

    async def test_get_events(self, client, auth_headers):
        response = await client.get("/api/v1/security/events", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_events_filter_severity(self, client, auth_headers):
        response = await client.get(
            "/api/v1/security/events?severity=high",
            headers=auth_headers
        )
        assert response.status_code == 200

    async def test_get_stats(self, client, auth_headers):
        response = await client.get("/api/v1/security/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "blocked_ips" in data

    async def test_resolve_event(self, client, auth_headers):
        create_res = await client.post(
            "/api/v1/security/events?event_type=test&description=To resolve&severity=low"
        )
        event_id = create_res.json()["id"]
        response = await client.patch(
            f"/api/v1/security/events/{event_id}/resolve",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestRateLimit:
    async def test_check_rate_limit(self, client, auth_headers):
        response = await client.post(
            "/api/v1/security/check/rate-limit?endpoint=/api/v1/auth/login",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_blocked" in data
        assert "requests_this_minute" in data

    async def test_check_ip(self, client, auth_headers):
        response = await client.post(
            "/api/v1/security/check/ip?ip_address=192.168.1.100",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "blocked" in response.json()

    async def test_block_and_unblock_ip(self, client, auth_headers):
        response = await client.post(
            "/api/v1/security/block/ip?ip_address=10.0.0.1&reason=test&duration_minutes=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["ip_address"] == "10.0.0.1"

        unblock = await client.delete(
            "/api/v1/security/block/ip/10.0.0.1",
            headers=auth_headers
        )
        assert unblock.status_code == 200

    async def test_get_blocked_ips(self, client, auth_headers):
        response = await client.get("/api/v1/security/blocks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
