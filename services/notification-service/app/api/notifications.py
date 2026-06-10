from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import get_db
from app.providers.push import push_provider
from app.providers.email import email_provider
from app.providers.sms import sms_provider
from app.models.notification import Notification
from app.schemas.notification import (
    SendPushRequest, SendEmailRequest, SendSMSRequest,
    NotificationResponse, SendResult,
)
from app.utils.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/push", response_model=SendResult)
async def send_push(payload: SendPushRequest, current_user: dict = Depends(get_current_user)):
    result = await push_provider.send(token=payload.token, title=payload.title, body=payload.body, data=payload.data)
    return SendResult(**result)


@router.post("/email", response_model=SendResult)
async def send_email(payload: SendEmailRequest, current_user: dict = Depends(get_current_user)):
    result = await email_provider.send_template(to_email=payload.to_email, template_name=payload.template, variables=payload.variables)
    return SendResult(**result)


@router.post("/sms", response_model=SendResult)
async def send_sms(payload: SendSMSRequest, current_user: dict = Depends(get_current_user)):
    result = await sms_provider.send(to_phone=payload.to_phone, message=payload.message)
    return SendResult(**result)


@router.get("", response_model=list[NotificationResponse])
async def get_my_notifications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
):
    query = select(Notification).where(
        Notification.user_id == current_user["id"]
    ).order_by(Notification.created_at.desc()).limit(50)
    if unread_only:
        query = query.where(Notification.is_read == False)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == current_user["id"])
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "Notification marquée comme lue"}


@router.patch("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Notification).where(Notification.user_id == current_user["id"]).values(is_read=True)
    )
    await db.commit()
    return {"message": "Toutes les notifications marquées comme lues"}
