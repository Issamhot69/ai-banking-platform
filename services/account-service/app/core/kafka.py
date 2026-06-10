import json
import asyncio
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.core.config import settings

_producer: KafkaProducer = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retries=3,
            acks="all",
        )
    return _producer


async def publish_event(topic: str, key: str, payload: dict):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _publish_sync, topic, key, payload)


def _publish_sync(topic: str, key: str, payload: dict):
    try:
        producer = get_producer()
        future = producer.send(topic, key=key, value=payload)
        future.get(timeout=10)
    except KafkaError as e:
        print(f"❌ Kafka error: {e}")
