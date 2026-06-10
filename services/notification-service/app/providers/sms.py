from app.core.config import settings


class SMSProvider:
    def __init__(self):
        self.client = None
        self._init_twilio()

    def _init_twilio(self):
        try:
            from twilio.rest import Client
            if settings.TWILIO_ACCOUNT_SID != "your_twilio_sid":
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                print("✅ Twilio initialisé")
            else:
                print("⚠️  Twilio en mode simulé")
        except Exception as e:
            print(f"⚠️  Twilio désactivé: {e}")

    async def send(self, to_phone: str, message: str) -> dict:
        if not self.client:
            print(f"📱 [SIMULATION] SMS → {to_phone}: {message}")
            return {"success": True, "simulated": True}
        try:
            msg = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_FROM_NUMBER,
                to=to_phone,
            )
            return {"success": True, "sid": msg.sid, "status": msg.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_otp(self, to_phone: str, otp_code: str) -> dict:
        message = f"AI Banking: Votre code est {otp_code}. Valable 5 minutes."
        return await self.send(to_phone, message)

    async def send_transaction_alert(self, to_phone: str, amount: float, currency: str) -> dict:
        message = f"AI Banking: Transaction de {amount} {currency} effectuée."
        return await self.send(to_phone, message)


sms_provider = SMSProvider()
