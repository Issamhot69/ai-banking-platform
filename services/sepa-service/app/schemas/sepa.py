from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid

class SEPATransferRequest(BaseModel):
    from_account_id: uuid.UUID
    debtor_name: str
    debtor_iban: str
    creditor_name: str
    creditor_iban: str
    creditor_bic: Optional[str] = None
    amount: Decimal
    remittance_info: Optional[str] = None
    purpose_code: Optional[str] = None
    is_instant: bool = False

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Le montant doit être positif")
        if v > Decimal("999999.99"):
            raise ValueError("Montant maximum: 999,999.99 EUR")
        return v

    @field_validator("creditor_iban", "debtor_iban")
    @classmethod
    def validate_iban(cls, v):
        iban = v.replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            raise ValueError("IBAN invalide")
        return iban

class SEPATransferResponse(BaseModel):
    id: uuid.UUID
    reference: str
    end_to_end_id: str
    user_id: uuid.UUID
    from_account_id: uuid.UUID
    debtor_name: str
    debtor_iban: str
    debtor_bic: str
    creditor_name: str
    creditor_iban: str
    creditor_bic: Optional[str]
    creditor_country: str
    amount: Decimal
    currency: str
    fee: Decimal
    transfer_type: str
    is_instant: bool
    remittance_info: Optional[str]
    purpose_code: Optional[str]
    status: str
    rejection_reason: Optional[str]
    submitted_at: datetime
    processed_at: Optional[datetime]
    settlement_date: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
