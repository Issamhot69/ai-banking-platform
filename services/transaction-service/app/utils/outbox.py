from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outbox import OutboxEvent


async def enqueue_event(db: AsyncSession, topic: str, key: str, payload: dict) -> None:
    """Insère un événement dans l'outbox — dans la même transaction que l'opération métier.
    Garantit qu'aucun événement n'est perdu même si le service plante après le commit."""
    event = OutboxEvent(topic=topic, key=key, payload=payload)
    db.add(event)
