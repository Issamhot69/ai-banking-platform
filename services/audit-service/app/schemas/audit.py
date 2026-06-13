from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class AuditLogCreate(BaseModel):
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    status: str = "success"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: dict = {}
    response_data: dict = {}
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    service: str
    severity: str = "info"

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[str]
    user_email: Optional[str]
    action: str
    resource: str
    resource_id: Optional[str]
    status: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: dict
    response_data: dict
    error_message: Optional[str]
    duration_ms: Optional[int]
    service: str
    severity: str
    created_at: datetime

    model_config = {"from_attributes": True}

class AuditStatsResponse(BaseModel):
    total_logs: int
    success_count: int
    error_count: int
    warning_count: int
    by_service: dict
    by_action: dict
    recent_errors: list
