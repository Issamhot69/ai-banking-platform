from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid

class CreateCardRequest(BaseModel):
    account_id: uuid.UUID
    card_holder_name: str
    card_type: str = "visa"
    daily_limit: Optional[Decimal] = Decimal("1000.00")
    monthly_limit: Optional[Decimal] = Decimal("5000.00")

class CardResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    card_number_masked: str
    card_holder_name: str
    expiry_month: int
    expiry_year: int
    card_type: str
    status: str
    daily_limit: Decimal
    monthly_limit: Decimal
    daily_spent: Decimal
    monthly_spent: Decimal
    is_virtual: bool
    is_contactless: bool
    is_online_enabled: bool
    is_international_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class CardDetailsResponse(CardResponse):
    card_number: str
    cvv: Optional[str] = None

class UpdateCardRequest(BaseModel):
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    is_online_enabled: Optional[bool] = None
    is_international_enabled: Optional[bool] = None
    is_contactless: Optional[bool] = None
