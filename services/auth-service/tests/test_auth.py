import pytest
from httpx import AsyncClient


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client, test_user_data):
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user_data):
        await client.post("/api/v1/auth/register", json=test_user_data)
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "weak@bank.com",
            "password": "123",
            "first_name": "Test",
            "last_name": "User"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Test@1234",
            "first_name": "Test",
            "last_name": "User"
        })
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client, registered_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, registered_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPassword@123"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "unknown@bank.com",
            "password": "Test@1234"
        })
        assert response.status_code == 401


class TestJWT:
    @pytest.mark.asyncio
    async def test_get_me_with_valid_token(self, client, registered_user, auth_headers):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == registered_user["email"]

    @pytest.mark.asyncio
    async def test_get_me_without_token(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token(self, client):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client, logged_in_user):
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": logged_in_user["refresh_token"]
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSecurity:
    @pytest.mark.asyncio
    async def test_password_not_in_response(self, client, test_user_data):
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert test_user_data["password"] not in response.text
        assert "password_hash" not in response.text

    @pytest.mark.asyncio
    async def test_logout(self, client, auth_headers):
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "Déconnexion" in response.json()["message"]
