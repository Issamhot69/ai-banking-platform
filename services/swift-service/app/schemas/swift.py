from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid

class SWIFTTransferRequest(BaseModel):
    from_account_id: uuid.UUID
    sender_name: str
    sender_address: Optional[str] = None
    sender_country: str = "MA"

    beneficiary_name: str
    beneficiary_address: Optional[str] = None
    beneficiary_country: str
    beneficiary_account: str
    beneficiary_bank_name: str
    beneficiary_bic: str

    amount: Decimal
    currency: str
    purpose_code: Optional[str] = None
    remittance_info: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Le montant doit être positif")
        if v > Decimal("1000000"):
            raise ValueError("Montant maximum: 1,000,000")
        return v

    @field_validator("beneficiary_bic")
    @classmethod
    def validate_bic(cls, v):
        v = v.upper().strip()
        if len(v) not in [8, 11]:
            raise ValueError("BIC invalide — doit avoir 8 ou 11 caractères")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        allowed = ["EUR", "USD", "GBP", "MAD", "CHF", "JPY", "CAD", "AUD"]
        if v.upper() not in allowed:
            raise ValueError(f"Devise non supportée. Devises acceptées: {', '.join(allowed)}")
        return v.upper()

class SWIFTTransferResponse(BaseModel):
    id: uuid.UUID
    reference: str
    user_id: uuid.UUID
    from_account_id: uuid.UUID
    sender_name: str
    sender_country: str
    beneficiary_name: str
    beneficiary_country: str
    beneficiary_account: str
    beneficiary_bank_name: str
    beneficiary_bic: str
    amount: Decimal
    currency: str
    exchange_rate: Decimal
    amount_in_eur: Decimal
    fee: Decimal
    total_deducted: Decimal
    message_type: str
    purpose_code: Optional[str]
    remittance_info: Optional[str]
    status: str
    aml_status: str
    aml_flags: dict
    rejection_reason: Optional[str]
    submitted_at: datetime
    processed_at: Optional[datetime]
    estimated_arrival: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

class ExchangeRateResponse(BaseModel):
    from_currency: str
    to_currency: str
    rate: Decimal
    amount: Decimal
    converted_amount: Decimal
    fee: Decimal
    total: Decimal
