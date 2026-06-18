import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.database import engine
from app.core.kafka import publish_event
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def publish_pending_events():
    """Lit les événements non publiés de l'outbox et les envoie sur Kafka.
    Appelée toutes les 5 secondes par le planificateur — garantit la livraison
    même si le service plantait juste après un commit."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.published == False)
            .order_by(OutboxEvent.created_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()

        for event in events:
            try:
                await publish_event(event.topic, event.key, event.payload)
                event.published = True
                event.published_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"Échec publication événement {event.id}: {e}")

        await db.commit()
        return len(events)

# Métrique Prometheus pour surveiller l'outbox
from prometheus_client import Gauge, Counter

outbox_pending_gauge = Gauge(
    'transaction_outbox_pending_events',
    'Number of unpublished events in the outbox'
)
outbox_published_counter = Counter(
    'transaction_outbox_published_total',
    'Total events successfully published from outbox'
)
outbox_failed_counter = Counter(
    'transaction_outbox_failed_total',
    'Total events that failed to publish from outbox'
)
