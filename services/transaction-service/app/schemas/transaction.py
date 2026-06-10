from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid


class TransferRequest(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    currency: str = "EUR"
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


class PaymentRequest(BaseModel):
    account_id: uuid.UUID
    amount: Decimal
    currency: str = "EUR"
    description: str
    merchant: Optional[str] = None
    category: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Le montant doit être positif")
        return v


class TransactionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    to_account_id: Optional[uuid.UUID]
    type: str
    amount: Decimal
    currency: str
    description: Optional[str]
    reference: Optional[str]
    status: str
    risk_score: int
    fraud_flags: list
    balance_before: Optional[Decimal]
    balance_after: Optional[Decimal]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    transactions: list[TransactionResponse]


class TransactionStatsResponse(BaseModel):
    total_credited: Decimal
    total_debited: Decimal
    total_transactions: int
    avg_transaction: Decimal
    flagged_count: int
