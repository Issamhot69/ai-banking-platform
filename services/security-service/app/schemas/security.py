from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class IPBlockResponse(BaseModel):
    id: uuid.UUID
    ip_address: str
    reason: str
    failed_attempts: int
    is_permanent: bool
    blocked_until: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}

class SecurityEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    severity: str
    ip_address: Optional[str]
    user_id: Optional[str]
    description: str
    extra_data: dict
    resolved: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class RateLimitStatus(BaseModel):
    ip_address: str
    endpoint: str
    requests_this_minute: int
    requests_this_hour: int
    limit_per_minute: int
    limit_per_hour: int
    is_blocked: bool
    blocked_until: Optional[str]

class SecurityStatsResponse(BaseModel):
    total_events: int
    critical_events: int
    blocked_ips: int
    events_by_type: dict
    recent_events: list
