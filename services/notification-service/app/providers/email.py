from app.core.config import settings

TEMPLATES = {
    "welcome": {
        "subject": "Bienvenue sur AI Banking Platform 🏦",
        "body": "Bonjour {first_name},\n\nBienvenue sur AI Banking Platform !\nVotre compte a été créé avec succès.\n\nL'équipe AI Banking",
    },
    "transaction": {
        "subject": "Transaction confirmée — {amount} {currency}",
        "body": "Bonjour {first_name},\n\nTransaction traitée:\nType: {transaction_type}\nMontant: {amount} {currency}\nRéférence: {reference}\nStatut: {status}\n\nL'équipe AI Banking",
    },
    "fraud_alert": {
        "subject": "⚠️ Alerte sécurité — Activité suspecte détectée",
        "body": "Bonjour {first_name},\n\nActivité suspecte détectée.\nMontant: {amount} {currency}\nScore de risque: {risk_score}/100\n\nTransaction temporairement bloquée.\n\nL'équipe Sécurité AI Banking",
    },
    "kyc_approved": {
        "subject": "✅ Votre identité a été vérifiée",
        "body": "Bonjour {first_name},\n\nVotre vérification KYC a été approuvée.\nVous avez accès à toutes les fonctionnalités.\n\nL'équipe AI Banking",
    },
}


class EmailProvider:
    def __init__(self):
        self.client = None
        self._init_sendgrid()

    def _init_sendgrid(self):
        try:
            from sendgrid import SendGridAPIClient
            if settings.SENDGRID_API_KEY != "your_sendgrid_api_key":
                self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                print("✅ SendGrid initialisé")
            else:
                print("⚠️  SendGrid en mode simulé")
        except Exception as e:
            print(f"⚠️  SendGrid désactivé: {e}")

    async def send(self, to_email: str, subject: str, body: str) -> dict:
        if not self.client:
            print(f"📧 [SIMULATION] Email → {to_email}: {subject}")
            return {"success": True, "simulated": True}
        try:
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email=(settings.FROM_EMAIL, settings.FROM_NAME),
                to_emails=to_email,
                subject=subject,
                plain_text_content=body,
            )
            response = self.client.send(message)
            return {"success": True, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_template(self, to_email: str, template_name: str, variables: dict) -> dict:
        template = TEMPLATES.get(template_name)
        if not template:
            return {"success": False, "error": f"Template {template_name} introuvable"}
        subject = template["subject"].format(**variables)
        body = template["body"].format(**variables)
        return await self.send(to_email, subject, body)


email_provider = EmailProvider()
