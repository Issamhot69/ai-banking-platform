from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import uuid

from app.core.database import get_db
from app.models.loan import LoanApplication, LoanRepayment
from app.schemas.loan import (
    LoanApplicationRequest, LoanApplicationResponse,
    LoanRepaymentResponse, LoanSimulationRequest, LoanSimulationResponse
)
from app.utils.dependencies import get_current_user
from app.utils.loan_calculator import (
    calculate_interest_rate, calculate_monthly_payment,
    generate_amortization_schedule, assess_creditworthiness
)

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/simulate", response_model=LoanSimulationResponse)
async def simulate_loan(
    payload: LoanSimulationRequest,
    current_user: dict = Depends(get_current_user),
):
    credit_score = 700
    interest_rate = calculate_interest_rate(payload.loan_type, credit_score, "employed")
    monthly_payment = calculate_monthly_payment(payload.amount, interest_rate, payload.term_months)
    total_repayment = (monthly_payment * payload.term_months).quantize(Decimal("0.01"))
    total_interest = (total_repayment - payload.amount).quantize(Decimal("0.01"))
    schedule = generate_amortization_schedule(payload.amount, interest_rate, payload.term_months, monthly_payment)

    return LoanSimulationResponse(
        amount=payload.amount,
        term_months=payload.term_months,
        interest_rate=interest_rate,
        monthly_payment=monthly_payment,
        total_repayment=total_repayment,
        total_interest=total_interest,
        schedule=schedule[:3],
    )


@router.post("/apply", response_model=LoanApplicationResponse, status_code=201)
async def apply_for_loan(
    payload: LoanApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier pas de prêt actif
    existing = await db.execute(
        select(LoanApplication).where(
            LoanApplication.user_id == current_user["id"],
            LoanApplication.status.in_(["pending", "approved", "disbursed"])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Un prêt actif existe déjà")

    # Évaluation crédit
    assessment = assess_creditworthiness(
        payload.monthly_income, payload.amount_requested,
        payload.term_months, payload.employment_status
    )

    credit_score = assessment["score"] * 8
    interest_rate = calculate_interest_rate(payload.loan_type, credit_score, payload.employment_status)
    monthly_payment = calculate_monthly_payment(payload.amount_requested, interest_rate, payload.term_months)
    total_repayment = (monthly_payment * payload.term_months).quantize(Decimal("0.01"))

    loan_status = "approved" if assessment["approved"] else "rejected"

    loan = LoanApplication(
        user_id=current_user["id"],
        account_id=payload.account_id,
        loan_type=payload.loan_type,
        amount_requested=payload.amount_requested,
        term_months=payload.term_months,
        purpose=payload.purpose,
        monthly_income=payload.monthly_income,
        employment_status=payload.employment_status,
        credit_score=credit_score,
        interest_rate=interest_rate if assessment["approved"] else None,
        monthly_payment=monthly_payment if assessment["approved"] else None,
        total_repayment=total_repayment if assessment["approved"] else None,
        status=loan_status,
        rejection_reason=None if assessment["approved"] else assessment["reason"],
        ai_assessment=assessment,
        approved_at=datetime.now(timezone.utc) if assessment["approved"] else None,
    )

    db.add(loan)
    await db.flush()

    # Générer échéancier si approuvé
    if assessment["approved"]:
        schedule = generate_amortization_schedule(
            payload.amount_requested, interest_rate, payload.term_months, monthly_payment
        )
        for item in schedule:
            repayment = LoanRepayment(
                loan_id=loan.id,
                user_id=current_user["id"],
                installment_number=item["installment"],
                amount=Decimal(item["payment"]),
                principal=Decimal(item["principal"]),
                interest=Decimal(item["interest"]),
                due_date=datetime.strptime(item["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc),
            )
            db.add(repayment)

    await db.commit()
    await db.refresh(loan)
    return loan


@router.get("/my-loans", response_model=list[LoanApplicationResponse])
async def get_my_loans(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LoanApplication)
        .where(LoanApplication.user_id == current_user["id"])
        .order_by(desc(LoanApplication.created_at))
    )
    return result.scalars().all()


@router.get("/{loan_id}", response_model=LoanApplicationResponse)
async def get_loan(
    loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LoanApplication).where(
            LoanApplication.id == loan_id,
            LoanApplication.user_id == current_user["id"]
        )
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Prêt introuvable")
    return loan


@router.get("/{loan_id}/schedule", response_model=list[LoanRepaymentResponse])
async def get_repayment_schedule(
    loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LoanRepayment)
        .where(
            LoanRepayment.loan_id == loan_id,
            LoanRepayment.user_id == current_user["id"]
        )
        .order_by(LoanRepayment.installment_number)
    )
    return result.scalars().all()


@router.post("/{loan_id}/disburse", response_model=LoanApplicationResponse)
async def disburse_loan(
    loan_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LoanApplication).where(
            LoanApplication.id == loan_id,
            LoanApplication.user_id == current_user["id"]
        )
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Prêt introuvable")
    if loan.status != "approved":
        raise HTTPException(status_code=400, detail="Prêt non approuvé")

    from sqlalchemy import text
    await db.execute(
        text("UPDATE accounts SET balance = balance + :amount, available_balance = available_balance + :amount WHERE id = :id"),
        {"amount": float(loan.amount_requested), "id": str(loan.account_id)}
    )

    loan.status = "disbursed"
    loan.disbursed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(loan)
    return loan
