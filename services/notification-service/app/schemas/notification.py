from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class SendPushRequest(BaseModel):
    user_id: str
    token: str
    title: str
    body: str
    data: Optional[dict] = None


class SendEmailRequest(BaseModel):
    to_email: str
    template: str
    variables: dict


class SendSMSRequest(BaseModel):
    to_phone: str
    message: str


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    channel: str
    title: str
    body: Optional[str]
    is_read: bool
    is_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SendResult(BaseModel):
    success: bool
    simulated: Optional[bool] = None
    error: Optional[str] = None
    message_id: Optional[str] = None
