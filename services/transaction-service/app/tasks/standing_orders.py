import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import engine
from app.core.kafka import publish_event
from app.models.standing_order import StandingOrder
from app.models.transaction import Transaction
from app.utils.reference import generate_reference

logger = logging.getLogger(__name__)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def _next_date(current: datetime, frequency: str) -> datetime:
    if frequency == "daily":
        return current + timedelta(days=1)
    if frequency == "weekly":
        return current + timedelta(weeks=1)
    if frequency == "monthly":
        return current + relativedelta(months=1)
    return current + timedelta(days=1)


async def execute_due_standing_orders():
    """Appelée périodiquement par le planificateur — exécute tous les ordres permanents arrivés à échéance."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(StandingOrder)
            .where(StandingOrder.status == "active", StandingOrder.next_execution_date <= now)
            .with_for_update(skip_locked=True)
        )
        due_orders = result.scalars().all()

        for order in due_orders:
            try:
                await _execute_one(db, order, now)
            except Exception as e:
                logger.error(f"Échec d'exécution de l'ordre permanent {order.id}: {e}")
                await db.rollback()

        return len(due_orders)


async def _execute_one(db: AsyncSession, order: StandingOrder, now: datetime):
    from_row = (await db.execute(text("SELECT * FROM accounts WHERE id = :id"), {"id": str(order.from_account_id)})).mappings().first()
    if not from_row:
        order.status = "cancelled"
        await db.commit()
        return

    if Decimal(str(from_row["available_balance"])) < order.amount:
        # Solde insuffisant : on reporte à la prochaine échéance sans débiter
        order.next_execution_date = _next_date(order.next_execution_date, order.frequency)
        await db.commit()
        return

    to_row = (await db.execute(text("SELECT * FROM accounts WHERE id = :id"), {"id": str(order.to_account_id)})).mappings().first()
    if not to_row:
        order.status = "cancelled"
        await db.commit()
        return

    balance_before = Decimal(str(from_row["available_balance"]))
    balance_after = balance_before - order.amount

    tx = Transaction(
        account_id=order.from_account_id,
        to_account_id=order.to_account_id,
        type="standing_order",
        amount=order.amount,
        currency=order.currency,
        description=order.description or f"Virement permanent vers {to_row['account_number']}",
        reference=generate_reference("STO"),
        status="completed",
        risk_score=0,
        fraud_flags=[],
        balance_before=balance_before,
        balance_after=balance_after,
    )
    db.add(tx)

    await db.execute(
        text("UPDATE accounts SET balance = balance - :amount, available_balance = available_balance - :amount, updated_at = NOW() WHERE id = :id"),
        {"amount": float(order.amount), "id": str(order.from_account_id)},
    )
    await db.execute(
        text("UPDATE accounts SET balance = balance + :amount, available_balance = available_balance + :amount, updated_at = NOW() WHERE id = :id"),
        {"amount": float(order.amount), "id": str(order.to_account_id)},
    )

    order.last_executed_at = now
    order.execution_count += 1
    order.next_execution_date = _next_date(order.next_execution_date, order.frequency)

    await db.commit()
    await db.refresh(tx)

    await publish_event("transaction.created", str(tx.id), {
        "event": "standing_order.executed",
        "standing_order_id": str(order.id),
        "transaction_id": str(tx.id),
        "amount": float(order.amount),
    })
