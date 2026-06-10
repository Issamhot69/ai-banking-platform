import json
import asyncio
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from app.core.config import settings
from app.providers.push import push_provider
from app.providers.email import email_provider
from app.providers.sms import sms_provider

TOPICS = [
    "transaction.created",
    "transaction.reversed",
    "fraud.detected",
    "account.created",
    "account.frozen",
]


class NotificationConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False

    def _create_consumer(self):
        return KafkaConsumer(
            *TOPICS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="notification-service",
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )

    async def start(self):
        self.running = True
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._consume_loop)

    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()

    def _consume_loop(self):
        try:
            self.consumer = self._create_consumer()
            print(f"✅ Kafka consumer démarré — topics: {TOPICS}")
            for message in self.consumer:
                if not self.running:
                    break
                try:
                    asyncio.run(self._handle_event(message.topic, message.value))
                except Exception as e:
                    print(f"❌ Erreur event: {e}")
        except KafkaError as e:
            print(f"⚠️  Kafka consumer erreur: {e}")

    async def _handle_event(self, topic: str, event: dict):
        handlers = {
            "transaction.created": self._on_transaction,
            "transaction.reversed": self._on_reversal,
            "fraud.detected": self._on_fraud,
            "account.created": self._on_account_created,
            "account.frozen": self._on_account_frozen,
        }
        handler = handlers.get(topic)
        if handler:
            await handler(event)

    async def _on_transaction(self, event: dict):
        amount = event.get("amount", 0)
        currency = event.get("currency", "EUR")
        tx_type = event.get("event", "transaction")
        title = "Transaction effectuée ✅"
        body = f"{amount} {currency} — {tx_type.replace('transaction.', '').title()}"
        print(f"🔔 {title}: {body}")

    async def _on_fraud(self, event: dict):
        risk_score = event.get("risk_score", 0)
        flags = event.get("flags", [])
        title = "⚠️ Alerte Fraude Détectée"
        body = f"Activité suspecte — Score: {risk_score}/100"
        print(f"🚨 {title}: {body} — Flags: {flags}")

    async def _on_reversal(self, event: dict):
        print(f"🔄 Transaction reversée: {event.get('transaction_id')}")

    async def _on_account_created(self, event: dict):
        print(f"🏦 Nouveau compte: {event.get('account_type')} [{event.get('currency')}]")

    async def _on_account_frozen(self, event: dict):
        print(f"🔒 Compte gelé: {event.get('account_id')} — {event.get('reason')}")


notification_consumer = NotificationConsumer()
