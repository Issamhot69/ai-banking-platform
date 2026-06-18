from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid


class StandingOrderCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    currency: str = "EUR"
    frequency: str
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Le montant doit être positif")
        if v > Decimal("50000"):
            raise ValueError("Montant maximum: 50,000")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        allowed = ["EUR", "USD", "GBP", "MAD", "CHF"]
        if v.upper() not in allowed:
            raise ValueError("Devise non supportée")
        return v.upper()

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        allowed = ["daily", "weekly", "monthly"]
        if v.lower() not in allowed:
            raise ValueError("Fréquence invalide: daily, weekly ou monthly")
        return v.lower()


class StandingOrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    currency: str
    frequency: str
    description: Optional[str]
    status: str
    next_execution_date: datetime
    last_executed_at: Optional[datetime]
    execution_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StandingOrderListResponse(BaseModel):
    standing_orders: list[StandingOrderResponse]
