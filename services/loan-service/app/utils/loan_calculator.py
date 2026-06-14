from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from app.core.config import settings

LOAN_TYPE_RATES = {
    "personal": Decimal("8.5"),
    "mortgage": Decimal("4.5"),
    "auto": Decimal("6.5"),
    "business": Decimal("7.5"),
    "education": Decimal("5.5"),
}

EMPLOYMENT_MULTIPLIER = {
    "employed": Decimal("1.0"),
    "self_employed": Decimal("1.2"),
    "unemployed": Decimal("1.8"),
    "retired": Decimal("1.1"),
}

def calculate_interest_rate(loan_type: str, credit_score: int, employment_status: str) -> Decimal:
    base_rate = LOAN_TYPE_RATES.get(loan_type, Decimal("8.5"))
    
    if credit_score >= 750:
        score_adjustment = Decimal("-1.5")
    elif credit_score >= 700:
        score_adjustment = Decimal("-0.5")
    elif credit_score >= 650:
        score_adjustment = Decimal("0")
    elif credit_score >= 600:
        score_adjustment = Decimal("1.5")
    else:
        score_adjustment = Decimal("3.0")

    emp_multiplier = EMPLOYMENT_MULTIPLIER.get(employment_status, Decimal("1.0"))
    rate = (base_rate + score_adjustment) * emp_multiplier
    return max(rate, Decimal("3.0")).quantize(Decimal("0.01"))


def calculate_monthly_payment(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
    if annual_rate == 0:
        return (principal / term_months).quantize(Decimal("0.01"))
    
    monthly_rate = annual_rate / Decimal("100") / Decimal("12")
    factor = (1 + monthly_rate) ** term_months
    payment = principal * monthly_rate * factor / (factor - 1)
    return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_amortization_schedule(principal: Decimal, annual_rate: Decimal, term_months: int, monthly_payment: Decimal) -> list:
    schedule = []
    balance = principal
    monthly_rate = annual_rate / Decimal("100") / Decimal("12")
    start_date = datetime.now(timezone.utc)

    for i in range(1, term_months + 1):
        interest = (balance * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        principal_payment = (monthly_payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        if i == term_months:
            principal_payment = balance
            monthly_payment = principal_payment + interest

        balance = (balance - principal_payment).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        due_date = start_date + timedelta(days=30 * i)

        schedule.append({
            "installment": i,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "payment": str(monthly_payment),
            "principal": str(principal_payment),
            "interest": str(interest),
            "balance": str(max(balance, Decimal("0"))),
        })

    return schedule


def assess_creditworthiness(monthly_income: Decimal, amount: Decimal, term_months: int, employment_status: str) -> dict:
    monthly_payment_estimate = amount / term_months
    debt_to_income = monthly_payment_estimate / monthly_income * 100

    if employment_status == "unemployed":
        return {"approved": False, "reason": "Statut d'emploi: chômage", "score": 20}

    if debt_to_income > 50:
        return {"approved": False, "reason": f"Ratio dette/revenu trop élevé: {debt_to_income:.1f}%", "score": 30}

    if debt_to_income > 35:
        score = 60
        approved = True
        reason = "Approuvé avec conditions"
    elif debt_to_income > 20:
        score = 80
        approved = True
        reason = "Approuvé"
    else:
        score = 95
        approved = True
        reason = "Excellent profil"

    return {
        "approved": approved,
        "reason": reason,
        "score": score,
        "debt_to_income_ratio": float(debt_to_income),
    }
