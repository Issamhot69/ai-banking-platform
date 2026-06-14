from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid

class LoanApplicationRequest(BaseModel):
    account_id: uuid.UUID
    loan_type: str  # personal, mortgage, auto, business, education
    amount_requested: Decimal
    term_months: int
    purpose: str
    monthly_income: Decimal
    employment_status: str  # employed, self_employed, unemployed, retired

    @field_validator("loan_type")
    @classmethod
    def validate_type(cls, v):
        allowed = ["personal", "mortgage", "auto", "business", "education"]
        if v not in allowed:
            raise ValueError(f"Type doit être: {', '.join(allowed)}")
        return v

    @field_validator("amount_requested")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal("1000"):
            raise ValueError("Montant minimum: 1,000 EUR")
        if v > Decimal("100000"):
            raise ValueError("Montant maximum: 100,000 EUR")
        return v

    @field_validator("term_months")
    @classmethod
    def validate_term(cls, v):
        if v < 6 or v > 84:
            raise ValueError("Durée: entre 6 et 84 mois")
        return v

class LoanApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    loan_type: str
    amount_requested: Decimal
    term_months: int
    purpose: str
    monthly_income: Decimal
    employment_status: str
    credit_score: Optional[int]
    interest_rate: Optional[Decimal]
    monthly_payment: Optional[Decimal]
    total_repayment: Optional[Decimal]
    status: str
    rejection_reason: Optional[str]
    ai_assessment: dict
    approved_at: Optional[datetime]
    disbursed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}

class LoanRepaymentResponse(BaseModel):
    id: uuid.UUID
    loan_id: uuid.UUID
    installment_number: int
    amount: Decimal
    principal: Decimal
    interest: Decimal
    due_date: datetime
    paid_at: Optional[datetime]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class LoanSimulationRequest(BaseModel):
    amount: Decimal
    term_months: int
    loan_type: str = "personal"
    monthly_income: Optional[Decimal] = None

class LoanSimulationResponse(BaseModel):
    amount: Decimal
    term_months: int
    interest_rate: Decimal
    monthly_payment: Decimal
    total_repayment: Decimal
    total_interest: Decimal
    schedule: List[dict]
