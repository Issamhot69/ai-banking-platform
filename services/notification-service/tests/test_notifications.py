import pytest


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestPushNotification:
    @pytest.mark.asyncio
    async def test_send_push_success(self, client, auth_headers, test_user_id):
        response = await client.post(
            "/api/v1/notifications/push",
            json={
                "user_id": test_user_id,
                "token": "fake_fcm_token_123",
                "title": "Transfert effectué",
                "body": "Votre virement de 100 EUR a été effectué",
                "data": {"type": "transfer"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    @pytest.mark.asyncio
    async def test_send_push_without_token(self, client, test_user_id):
        response = await client.post(
            "/api/v1/notifications/push",
            json={
                "user_id": test_user_id,
                "token": "fake_token",
                "title": "Test",
                "body": "Test body",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_push_missing_fields(self, client, auth_headers):
        response = await client.post(
            "/api/v1/notifications/push",
            json={"title": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestEmailNotification:
    @pytest.mark.asyncio
    async def test_send_email_success(self, client, auth_headers):
        response = await client.post(
            "/api/v1/notifications/email",
            json={
                "to_email": "user@bank.com",
                "template": "welcome",
                "variables": {"first_name": "John"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # En simulation (pas d'API key SendGrid), success doit être True
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_transaction_template(self, client, auth_headers):
        response = await client.post(
            "/api/v1/notifications/email",
            json={
                "to_email": "user@bank.com",
                "template": "transaction",
                "variables": {"amount": "100.00", "reference": "TRF-12345", "currency": "EUR", "first_name": "John", "transaction_type": "transfer", "status": "completed"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_email_without_token(self, client):
        response = await client.post(
            "/api/v1/notifications/email",
            json={"to_email": "user@bank.com", "template": "welcome", "variables": {}},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_email_missing_fields(self, client, auth_headers):
        response = await client.post(
            "/api/v1/notifications/email",
            json={"to_email": "user@bank.com"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestSMSNotification:
    @pytest.mark.asyncio
    async def test_send_sms_success(self, client, auth_headers):
        response = await client.post(
            "/api/v1/notifications/sms",
            json={
                "to_phone": "+212600000000",
                "message": "Votre code de vérification est 123456",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_send_sms_without_token(self, client):
        response = await client.post(
            "/api/v1/notifications/sms",
            json={"to_phone": "+212600000000", "message": "Test"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_sms_missing_message(self, client, auth_headers):
        response = await client.post(
            "/api/v1/notifications/sms",
            json={"to_phone": "+212600000000"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetNotifications:
    @pytest.mark.asyncio
    async def test_get_notifications_empty(self, client, auth_headers):
        response = await client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_notifications_without_token(self, client):
        response = await client.get("/api/v1/notifications")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_notifications_unread_only(self, client, auth_headers):
        response = await client.get(
            "/api/v1/notifications",
            params={"unread_only": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestMarkAsRead:
    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, client, auth_headers, test_user_id):
        # Insérer une notification directement en DB via conftest engine
        import uuid as uuid_module
        from tests.conftest import TestSession
        from app.models.notification import Notification

        notif_id = uuid_module.uuid4()
        async with TestSession() as session:
            notif = Notification(
                id=notif_id,
                user_id=test_user_id,
                type="transaction",
                channel="push",
                title="Test notification",
                body="Test body",
                is_read=False,
                is_sent=True,
            )
            session.add(notif)
            await session.commit()

        response = await client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "lue" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, client, auth_headers):
        response = await client.patch(
            "/api/v1/notifications/read-all",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "marquées" in response.json()["message"].lower() or "Toutes" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_mark_as_read_without_token(self, client):
        import uuid as uuid_module
        response = await client.patch(f"/api/v1/notifications/{uuid_module.uuid4()}/read")
        assert response.status_code == 403
