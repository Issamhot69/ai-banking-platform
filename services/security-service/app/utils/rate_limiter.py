import time
from app.core.config import settings

async def check_rate_limit(redis, ip: str, endpoint: str, limit_per_minute: int = None, limit_per_hour: int = None) -> dict:
    limit_min = limit_per_minute or settings.RATE_LIMIT_PER_MINUTE
    limit_hour = limit_per_hour or settings.RATE_LIMIT_PER_HOUR

    now = int(time.time())
    minute_key = f"ratelimit:{ip}:{endpoint}:minute:{now // 60}"
    hour_key = f"ratelimit:{ip}:{endpoint}:hour:{now // 3600}"

    # Incrémenter compteurs
    minute_count = await redis.incr(minute_key)
    if minute_count == 1:
        await redis.expire(minute_key, 60)

    hour_count = await redis.incr(hour_key)
    if hour_count == 1:
        await redis.expire(hour_key, 3600)

    is_blocked = minute_count > limit_min or hour_count > limit_hour

    return {
        "ip": ip,
        "endpoint": endpoint,
        "minute_count": minute_count,
        "hour_count": hour_count,
        "limit_per_minute": limit_min,
        "limit_per_hour": limit_hour,
        "is_blocked": is_blocked,
    }


async def track_failed_attempt(redis, ip: str, action: str) -> int:
    key = f"failed:{ip}:{action}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, settings.BLOCK_DURATION_MINUTES * 60)
    return count


async def reset_failed_attempts(redis, ip: str, action: str):
    key = f"failed:{ip}:{action}"
    await redis.delete(key)


async def is_ip_blocked(redis, ip: str) -> dict:
    if ip in settings.WHITELISTED_IPS:
        return {"blocked": False, "reason": "whitelisted"}

    block_key = f"blocked:{ip}"
    blocked_until = await redis.get(block_key)

    if blocked_until:
        return {"blocked": True, "until": blocked_until, "reason": "too_many_failures"}

    return {"blocked": False}


async def block_ip(redis, ip: str, duration_minutes: int = None, reason: str = "too_many_failures"):
    duration = duration_minutes or settings.BLOCK_DURATION_MINUTES
    block_key = f"blocked:{ip}"
    import time
    blocked_until = int(time.time()) + (duration * 60)
    await redis.setex(block_key, duration * 60, str(blocked_until))
    return blocked_until
