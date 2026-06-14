from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta
import uuid

from app.core.database import get_db
from app.core.redis import get_redis
from app.models.security import IPBlock, SecurityEvent, RateLimitRule
from app.schemas.security import IPBlockResponse, SecurityEventResponse, RateLimitStatus, SecurityStatsResponse
from app.utils.dependencies import get_current_user
from app.utils.rate_limiter import check_rate_limit, is_ip_blocked, block_ip, track_failed_attempt
from app.core.config import settings

router = APIRouter(prefix="/security", tags=["Security"])


@router.post("/check/rate-limit", response_model=RateLimitStatus)
async def check_rate_limit_endpoint(
    endpoint: str,
    request: Request,
    redis=Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    ip = request.client.host
    result = await check_rate_limit(redis, ip, endpoint)

    return RateLimitStatus(
        ip_address=ip,
        endpoint=endpoint,
        requests_this_minute=result["minute_count"],
        requests_this_hour=result["hour_count"],
        limit_per_minute=result["limit_per_minute"],
        limit_per_hour=result["limit_per_hour"],
        is_blocked=result["is_blocked"],
        blocked_until=None,
    )


@router.post("/check/ip")
async def check_ip(
    ip_address: str,
    redis=Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    result = await is_ip_blocked(redis, ip_address)
    return {"ip": ip_address, **result}


@router.post("/block/ip", response_model=IPBlockResponse)
async def block_ip_endpoint(
    ip_address: str,
    reason: str,
    duration_minutes: int = 30,
    is_permanent: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    blocked_until_ts = await block_ip(redis, ip_address, duration_minutes, reason)
    blocked_until = datetime.fromtimestamp(blocked_until_ts, tz=timezone.utc) if not is_permanent else None

    block = IPBlock(
        ip_address=ip_address,
        reason=reason,
        is_permanent=is_permanent,
        blocked_until=blocked_until,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


@router.delete("/block/ip/{ip_address}")
async def unblock_ip(
    ip_address: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    block_key = f"blocked:{ip_address}"
    await redis.delete(block_key)
    return {"message": f"IP {ip_address} débloquée", "ip": ip_address}


@router.get("/blocks", response_model=list[IPBlockResponse])
async def get_blocked_ips(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IPBlock).order_by(desc(IPBlock.created_at)).limit(100)
    )
    return result.scalars().all()


@router.post("/events", response_model=SecurityEventResponse, status_code=201)
async def create_security_event(
    event_type: str,
    description: str,
    severity: str = "medium",
    ip_address: str = None,
    user_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        ip_address=ip_address,
        user_id=user_id,
        description=description,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/events", response_model=list[SecurityEventResponse])
async def get_security_events(
    severity: str = None,
    event_type: str = None,
    resolved: bool = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SecurityEvent).order_by(desc(SecurityEvent.created_at)).limit(100)
    if severity:
        query = query.where(SecurityEvent.severity == severity)
    if event_type:
        query = query.where(SecurityEvent.event_type == event_type)
    if resolved is not None:
        query = query.where(SecurityEvent.resolved == resolved)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/events/{event_id}/resolve")
async def resolve_event(
    event_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    event.resolved = True
    await db.commit()
    return {"message": "Événement résolu", "id": str(event_id)}


@router.get("/stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(SecurityEvent.id)))).scalar() or 0
    critical = (await db.execute(select(func.count(SecurityEvent.id)).where(SecurityEvent.severity == "critical"))).scalar() or 0
    blocked = (await db.execute(select(func.count(IPBlock.id)))).scalar() or 0

    type_result = await db.execute(
        select(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.event_type)
        .order_by(desc(func.count(SecurityEvent.id)))
        .limit(10)
    )
    by_type = {row[0]: row[1] for row in type_result.fetchall()}

    recent_result = await db.execute(
        select(SecurityEvent)
        .where(SecurityEvent.resolved == False)
        .order_by(desc(SecurityEvent.created_at))
        .limit(5)
    )
    recent = [
        {"type": e.event_type, "severity": e.severity, "ip": e.ip_address, "at": str(e.created_at)}
        for e in recent_result.scalars().all()
    ]

    return SecurityStatsResponse(
        total_events=total,
        critical_events=critical,
        blocked_ips=blocked,
        events_by_type=by_type,
        recent_events=recent,
    )
