from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid


class SavingsGoalCreate(BaseModel):
    goal_account_id: uuid.UUID
    source_account_id: uuid.UUID
    name: str
    target_amount: Optional[Decimal] = None
    round_up_enabled: bool = True
    round_up_multiple: Decimal = Decimal("1.00")

    @field_validator("round_up_multiple")
    @classmethod
    def validate_multiple(cls, v):
        allowed = [Decimal("1.00"), Decimal("5.00"), Decimal("10.00")]
        if v not in allowed:
            raise ValueError("round_up_multiple doit être 1.00, 5.00 ou 10.00")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Le nom de l'objectif est requis")
        return v.strip()


class SavingsGoalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_account_id: uuid.UUID
    source_account_id: uuid.UUID
    name: str
    target_amount: Optional[Decimal]
    current_amount: Decimal
    round_up_enabled: bool
    round_up_multiple: Decimal
    status: str
    contribution_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SavingsGoalListResponse(BaseModel):
    savings_goals: list[SavingsGoalResponse]
