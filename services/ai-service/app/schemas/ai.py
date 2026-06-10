from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class FraudCheckRequest(BaseModel):
    account_id: str
    amount: Decimal
    transaction_type: str = "transfer"
    daily_count: int = 0
    velocity_10min: int = 0
    avg_amount: float = 0.0
    balance_ratio: float = 0.0
    is_international: bool = False


class FraudCheckResponse(BaseModel):
    is_fraud: bool
    confidence: float
    risk_score: int
    flags: list[str]
    model_used: str


class CreditScoreRequest(BaseModel):
    user_id: str
    monthly_income: float
    payment_history_score: float = 0.8
    credit_utilization: float = 0.3
    months_account_open: int = 12
    recent_inquiries: int = 0
    credit_mix_score: float = 0.5


class CreditScoreResponse(BaseModel):
    score: int
    label: str
    grade: str
    interest_rate: float
    max_loan_amount: float
    factors: dict
    recommendations: list[str]


class RecommendationRequest(BaseModel):
    user_id: str
    avg_balance: float = 0.0
    monthly_income: float = 0.0
    monthly_spend: float = 0.0
    credit_score: int = 600
    has_savings_account: bool = False
    top_spending_categories: list[str] = []
    age: int = 30


class RecommendationResponse(BaseModel):
    user_segment: str
    total_recommendations: int
    recommendations: list[dict]
    next_best_action: Optional[dict]


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []
    user_context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    model: str
    tokens_used: int


class SpendingAnalysisRequest(BaseModel):
    user_id: str
    transactions: list[dict]


class SpendingAnalysisResponse(BaseModel):
    insights: Optional[list] = None
    categories: Optional[dict] = None
    trends: Optional[list] = None
    tips: Optional[list] = None
    health_score: Optional[int] = None
    raw_analysis: Optional[str] = None
