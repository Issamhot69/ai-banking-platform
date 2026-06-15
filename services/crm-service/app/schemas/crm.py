from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class CustomerProfileCreate(BaseModel):
    user_id: uuid.UUID
    segment: str = "standard"
    notes: Optional[str] = None
    preferred_channel: str = "app"
    assigned_agent: Optional[str] = None

class CustomerProfileUpdate(BaseModel):
    segment: Optional[str] = None
    notes: Optional[str] = None
    preferred_channel: Optional[str] = None
    assigned_agent: Optional[str] = None
    is_vip: Optional[bool] = None
    satisfaction_score: Optional[float] = None

class CustomerProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    segment: str
    lifetime_value: float
    risk_score: int
    satisfaction_score: float
    total_transactions: int
    preferred_channel: str
    notes: Optional[str]
    tags: list
    is_vip: bool
    assigned_agent: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class TicketCreate(BaseModel):
    subject: str
    description: str
    category: str
    priority: str = "medium"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    priority: Optional[str] = None

class TicketResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    ticket_number: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[str]
    resolution: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}

class InteractionCreate(BaseModel):
    interaction_type: str
    channel: str
    summary: str
    agent: Optional[str] = None

class InteractionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    interaction_type: str
    channel: str
    summary: str
    agent: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class CRMStatsResponse(BaseModel):
    total_customers: int
    vip_customers: int
    open_tickets: int
    resolved_tickets: int
    by_segment: dict
    avg_satisfaction: float
