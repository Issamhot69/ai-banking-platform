import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.database import engine
from app.core.kafka import publish_event
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

MAX_RETRIES = 5


async def publish_pending_events():
    """Lit les événements non publiés de l'outbox et les envoie sur Kafka.
    Après MAX_RETRIES échecs, l'événement est marqué comme dead (DLQ).
    skip_locked permet à plusieurs instances de tourner en parallèle sans collision."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.published == False,
                OutboxEvent.failed_at == None,
            )
            .order_by(OutboxEvent.created_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()

        published = 0
        dead = 0

        for event in events:
            try:
                await publish_event(event.topic, event.key, event.payload)
                event.published = True
                event.published_at = datetime.now(timezone.utc)
                published += 1
            except Exception as e:
                event.retry_count += 1
                logger.warning(f"Échec publication événement {event.id} (tentative {event.retry_count}/{MAX_RETRIES}): {e}")
                if event.retry_count >= MAX_RETRIES:
                    event.failed_at = datetime.now(timezone.utc)
                    dead += 1
                    logger.error(f"Événement {event.id} déplacé en DLQ après {MAX_RETRIES} tentatives — topic={event.topic}")

        await db.commit()

        if dead > 0:
            logger.error(f"DLQ: {dead} événement(s) abandonnés après {MAX_RETRIES} tentatives")

        return {"published": published, "dead": dead, "total": len(events)}


async def get_dlq_events():
    """Retourne les événements en Dead Letter Queue pour inspection manuelle."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.failed_at != None)
            .order_by(OutboxEvent.failed_at.desc())
            .limit(50)
        )
        return result.scalars().all()
