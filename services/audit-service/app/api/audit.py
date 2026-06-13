from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timezone
import uuid
import csv
import io

from app.core.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogResponse, AuditStatsResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("/logs", response_model=AuditLogResponse, status_code=201)
async def create_log(
    payload: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
):
    log = AuditLog(**payload.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(desc(AuditLog.created_at))

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if service:
        query = query.where(AuditLog.service == service)
    if severity:
        query = query.where(AuditLog.severity == severity)
    if status:
        query = query.where(AuditLog.status == status)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_log(
    log_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log introuvable")
    return log


@router.get("/stats", response_model=AuditStatsResponse)
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(AuditLog.id)))).scalar() or 0
    success = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.status == "success"))).scalar() or 0
    error = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.status == "error"))).scalar() or 0
    warning = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.severity == "warning"))).scalar() or 0

    # Par service
    service_result = await db.execute(
        select(AuditLog.service, func.count(AuditLog.id))
        .group_by(AuditLog.service)
    )
    by_service = {row[0]: row[1] for row in service_result.fetchall()}

    # Par action
    action_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(desc(func.count(AuditLog.id)))
        .limit(10)
    )
    by_action = {row[0]: row[1] for row in action_result.fetchall()}

    # Erreurs récentes
    recent_errors_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.status == "error")
        .order_by(desc(AuditLog.created_at))
        .limit(5)
    )
    recent_errors = [
        {"action": log.action, "service": log.service, "error": log.error_message, "at": str(log.created_at)}
        for log in recent_errors_result.scalars().all()
    ]

    return AuditStatsResponse(
        total_logs=total,
        success_count=success,
        error_count=error,
        warning_count=warning,
        by_service=by_service,
        by_action=by_action,
        recent_errors=recent_errors,
    )


@router.get("/export/csv")
async def export_csv(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.created_at)).limit(1000)
    )
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "user_email", "action", "resource", "status", "service", "severity", "ip_address", "created_at"])
    for log in logs:
        writer.writerow([log.id, log.user_id, log.user_email, log.action, log.resource, log.status, log.service, log.severity, log.ip_address, log.created_at])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
