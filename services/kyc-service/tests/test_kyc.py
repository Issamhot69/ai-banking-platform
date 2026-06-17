import pytest
import io


class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestKYCSubmit:
    async def test_submit_kyc_success(self, client, auth_headers):
        file_content = b"fake document content"
        response = await client.post(
            "/api/v1/kyc/submit",
            headers=auth_headers,
            data={
                "document_type": "national_id",
                "first_name": "Jean",
                "last_name": "Dupont",
                "document_number": "AB123456",
                "date_of_birth": "1990-01-15",
                "nationality": "Moroccan",
                "address": "123 Rue Hassan II, Casablanca",
            },
            files={"document_front": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "national_id"
        assert data["first_name"] == "Jean"
        assert data["status"] in ["pending", "in_review", "verified"]

    async def test_submit_duplicate_kyc(self, client, auth_headers):
        file_content = b"fake document"
        await client.post(
            "/api/v1/kyc/submit",
            headers=auth_headers,
            data={"document_type": "passport", "first_name": "Jean", "last_name": "Dupont"},
            files={"document_front": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        )
        response = await client.post(
            "/api/v1/kyc/submit",
            headers=auth_headers,
            data={"document_type": "passport", "first_name": "Jean", "last_name": "Dupont"},
            files={"document_front": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        )
        assert response.status_code == 400

    async def test_submit_without_token(self, client):
        response = await client.post("/api/v1/kyc/submit", data={"document_type": "passport"})
        assert response.status_code == 401


class TestKYCStatus:
    async def test_get_kyc_status(self, client, auth_headers):
        file_content = b"fake doc"
        await client.post(
            "/api/v1/kyc/submit",
            headers=auth_headers,
            data={"document_type": "driving_license", "first_name": "Test", "last_name": "User"},
            files={"document_front": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        )
        response = await client.get("/api/v1/kyc/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "document_type" in data

    async def test_get_status_no_application(self, client):
        import os
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        import uuid
        new_user_token = jwt.encode(
            {"sub": str(uuid.uuid4()), "email": "new_no_app@bank.com", "type": "access",
             "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
            os.environ["SECRET_KEY"], algorithm=os.environ.get("ALGORITHM", "HS256")
        )
        response = await client.get("/api/v1/kyc/status",
                                    headers={"Authorization": f"Bearer {new_user_token}"})
        assert response.status_code == 404


class TestKYCAdmin:
    async def test_list_applications(self, client, auth_headers):
        response = await client.get("/api/v1/kyc/admin/applications", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_kyc_stats(self, client, auth_headers):
        response = await client.get("/api/v1/kyc/admin/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "verified" in data
        assert "pending" in data
