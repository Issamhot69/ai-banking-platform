from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid


class CreateAccountRequest(BaseModel):
    account_type: str
    currency: str = "EUR"
    is_primary: bool = False

    @field_validator("account_type")
    @classmethod
    def validate_type(cls, v):
        allowed = ["checking", "savings", "business"]
        if v not in allowed:
            raise ValueError(f"Type doit être: {', '.join(allowed)}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        allowed = ["EUR", "USD", "GBP", "MAD", "CHF"]
        if v.upper() not in allowed:
            raise ValueError("Devise non supportée")
        return v.upper()


class AccountResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_number: str
    iban: Optional[str]
    account_type: str
    currency: str
    balance: Decimal
    available_balance: Decimal
    status: str
    is_primary: bool
    daily_transfer_limit: Decimal
    monthly_transfer_limit: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateLimitsRequest(BaseModel):
    daily_transfer_limit: Optional[Decimal] = None
    monthly_transfer_limit: Optional[Decimal] = None


class FreezeAccountRequest(BaseModel):
    reason: str


class AccountSummaryResponse(BaseModel):
    total_accounts: int
    total_balance: Decimal
    currencies: list[str]
    accounts: list[AccountResponse]
