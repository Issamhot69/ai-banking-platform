from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.transaction import Transaction
from app.core.config import settings
import redis.asyncio as aioredis


class FraudDetector:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis

    async def check(self, account_id: str, amount: Decimal, transaction_type: str) -> dict:
        flags = []
        risk_score = 0

        if amount > Decimal(str(settings.FRAUD_AMOUNT_THRESHOLD)):
            flags.append("high_amount")
            risk_score += 30

        daily_count = await self._get_daily_count(account_id)
        if daily_count >= settings.MAX_DAILY_TRANSFERS:
            flags.append("too_many_daily_transactions")
            risk_score += 40

        velocity = await self._check_velocity(account_id)
        if velocity > 5:
            flags.append("high_velocity")
            risk_score += 30

        return {
            "is_fraud": risk_score >= 70,
            "risk_score": risk_score,
            "flags": flags,
        }

    async def _get_daily_count(self, account_id: str) -> int:
        today = datetime.now(timezone.utc).date()
        result = await self.db.execute(
            select(func.count(Transaction.id)).where(
                Transaction.account_id == account_id,
                func.date(Transaction.created_at) == today,
                Transaction.status == "completed",
            )
        )
        return result.scalar() or 0

    async def _check_velocity(self, account_id: str) -> int:
        key = f"velocity:{account_id}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 600)
        return count
