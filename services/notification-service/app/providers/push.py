import os
from app.core.config import settings


class PushProvider:
    def __init__(self):
        self.app = None
        self._init_firebase()

    def _init_firebase(self):
        try:
            import firebase_admin
            from firebase_admin import credentials
            if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                self.app = firebase_admin.initialize_app(cred)
                print("✅ Firebase initialisé")
            else:
                print("⚠️  Firebase credentials non trouvés — mode simulé")
        except Exception as e:
            print(f"⚠️  Firebase désactivé: {e}")

    async def send(self, token: str, title: str, body: str, data: dict = None) -> dict:
        if not self.app:
            print(f"📱 [SIMULATION] Push → {title}: {body}")
            return {"success": True, "simulated": True}

        try:
            from firebase_admin import messaging
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
                android=messaging.AndroidConfig(priority="high"),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default", badge=1)
                    )
                ),
            )
            response = messaging.send(message)
            return {"success": True, "message_id": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_multicast(self, tokens: list[str], title: str, body: str, data: dict = None) -> dict:
        if not self.app:
            print(f"📱 [SIMULATION] Multicast → {len(tokens)} devices")
            return {"success_count": len(tokens), "failure_count": 0, "simulated": True}
        try:
            from firebase_admin import messaging
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            response = messaging.send_each_for_multicast(message)
            return {"success_count": response.success_count, "failure_count": response.failure_count}
        except Exception as e:
            return {"success": False, "error": str(e)}


push_provider = PushProvider()
