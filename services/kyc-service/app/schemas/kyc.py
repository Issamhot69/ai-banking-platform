from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class KYCSubmitRequest(BaseModel):
    document_type: str  # passport, national_id, driving_license
    document_number: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None

class KYCResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    document_type: str
    document_number: Optional[str]
    first_name: str
    last_name: str
    date_of_birth: Optional[str]
    nationality: Optional[str]
    address: Optional[str]
    document_front_url: Optional[str]
    document_back_url: Optional[str]
    selfie_url: Optional[str]
    ai_verification_result: dict
    rejection_reason: Optional[str]
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}

class KYCReviewRequest(BaseModel):
    action: str  # approve, reject
    reason: Optional[str] = None

class KYCStatsResponse(BaseModel):
    total: int
    pending: int
    in_review: int
    verified: int
    rejected: int
