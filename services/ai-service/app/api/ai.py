from fastapi import APIRouter, Depends, HTTPException
from app.ml.fraud.detector import fraud_detector
from app.ml.scoring.credit_score import credit_scorer
from app.ml.recommender.engine import recommendation_engine
from app.ml.nlp.chatbot import chatbot
from app.schemas.ai import (
    FraudCheckRequest, FraudCheckResponse,
    CreditScoreRequest, CreditScoreResponse,
    RecommendationRequest, RecommendationResponse,
    ChatRequest, ChatResponse,
    SpendingAnalysisRequest, SpendingAnalysisResponse,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI & Intelligence"])


@router.post("/fraud/check", response_model=FraudCheckResponse)
async def check_fraud(
    payload: FraudCheckRequest,
    current_user: dict = Depends(get_current_user),
):
    result = await fraud_detector.predict(payload.model_dump())
    return FraudCheckResponse(**result)


@router.post("/credit-score", response_model=CreditScoreResponse)
async def get_credit_score(
    payload: CreditScoreRequest,
    current_user: dict = Depends(get_current_user),
):
    result = credit_scorer.calculate(payload.model_dump())
    return CreditScoreResponse(**result)


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    payload: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
):
    result = recommendation_engine.recommend(payload.model_dump())
    return RecommendationResponse(**result)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = await chatbot.chat(
            message=payload.message,
            conversation_history=payload.conversation_history,
            user_context=payload.user_context,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur chatbot: {str(e)}")


@router.post("/spending-analysis", response_model=SpendingAnalysisResponse)
async def analyze_spending(
    payload: SpendingAnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = await chatbot.analyze_spending(payload.transactions)
        return SpendingAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {str(e)}")


@router.get("/status")
async def ai_status():
    return {
        "fraud_model": "rule_based" if fraud_detector.model is None else "tensorflow",
        "credit_scorer": "active",
        "recommender": "active",
        "chatbot": "claude-sonnet-4-20250514",
        "status": "operational",
    }
