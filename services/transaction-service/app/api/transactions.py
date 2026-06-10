from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from decimal import Decimal
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.kafka import publish_event
from app.core.fraud import FraudDetector
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransferRequest, PaymentRequest,
    TransactionResponse, TransactionListResponse, TransactionStatsResponse,
)
from app.utils.dependencies import get_current_user
from app.utils.reference import generate_reference
import redis.asyncio as aioredis

router = APIRouter(prefix="/transactions", tags=["Transactions"])


async def _get_account(account_id, user_id, db):
    result = await db.execute(
        text("SELECT * FROM accounts WHERE id = :id AND user_id = :uid AND status = 'active'"),
        {"id": str(account_id), "uid": str(user_id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Compte introuvable ou inactif")
    return row


async def _get_account_any(account_id, db):
    result = await db.execute(
        text("SELECT * FROM accounts WHERE id = :id AND status = 'active'"),
        {"id": str(account_id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Compte destinataire introuvable")
    return row


@router.post("/transfer", response_model=TransactionResponse, status_code=201)
async def transfer(
    payload: TransferRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    from_account = await _get_account(payload.from_account_id, current_user["id"], db)
    to_account = await _get_account_any(payload.to_account_id, db)

    if Decimal(str(from_account["available_balance"])) < payload.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant")

    if payload.amount > Decimal(str(from_account["daily_transfer_limit"])):
        raise HTTPException(status_code=400, detail="Limite journalière dépassée")

    detector = FraudDetector(db, redis)
    fraud_result = await detector.check(str(payload.from_account_id), payload.amount, "transfer")

    balance_before = Decimal(str(from_account["available_balance"]))
    balance_after = balance_before - payload.amount

    tx = Transaction(
        account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        type="transfer",
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description or f"Transfert vers {to_account['account_number']}",
        reference=generate_reference("TRF"),
        status="flagged" if fraud_result["is_fraud"] else "completed",
        risk_score=fraud_result["risk_score"],
        fraud_flags=fraud_result["flags"],
        balance_before=balance_before,
        balance_after=balance_after,
    )
    db.add(tx)

    if not fraud_result["is_fraud"]:
        await db.execute(
            text("UPDATE accounts SET balance = balance - :amount, available_balance = available_balance - :amount, updated_at = NOW() WHERE id = :id"),
            {"amount": float(payload.amount), "id": str(payload.from_account_id)},
        )
        await db.execute(
            text("UPDATE accounts SET balance = balance + :amount, available_balance = available_balance + :amount, updated_at = NOW() WHERE id = :id"),
            {"amount": float(payload.amount), "id": str(payload.to_account_id)},
        )

    await db.commit()
    await db.refresh(tx)

    await publish_event("transaction.created", str(tx.id), {
        "event": "transaction.transfer",
        "transaction_id": str(tx.id),
        "from_account": str(payload.from_account_id),
        "to_account": str(payload.to_account_id),
        "amount": float(payload.amount),
        "currency": payload.currency,
        "status": tx.status,
        "risk_score": fraud_result["risk_score"],
    })

    if fraud_result["is_fraud"]:
        await publish_event("fraud.detected", str(tx.id), {
            "event": "fraud.detected",
            "transaction_id": str(tx.id),
            "account_id": str(payload.from_account_id),
            "risk_score": fraud_result["risk_score"],
            "flags": fraud_result["flags"],
        })

    return tx


@router.post("/payment", response_model=TransactionResponse, status_code=201)
async def payment(
    payload: PaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    account = await _get_account(payload.account_id, current_user["id"], db)

    if Decimal(str(account["available_balance"])) < payload.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant")

    detector = FraudDetector(db, redis)
    fraud_result = await detector.check(str(payload.account_id), payload.amount, "payment")

    balance_before = Decimal(str(account["available_balance"]))
    balance_after = balance_before - payload.amount

    tx = Transaction(
        account_id=payload.account_id,
        type="payment",
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        reference=generate_reference("PAY"),
        status="flagged" if fraud_result["is_fraud"] else "completed",
        risk_score=fraud_result["risk_score"],
        fraud_flags=fraud_result["flags"],
        balance_before=balance_before,
        balance_after=balance_after,
        metadata={"merchant": payload.merchant, "category": payload.category},
    )
    db.add(tx)

    if not fraud_result["is_fraud"]:
        await db.execute(
            text("UPDATE accounts SET balance = balance - :amount, available_balance = available_balance - :amount, updated_at = NOW() WHERE id = :id"),
            {"amount": float(payload.amount), "id": str(payload.account_id)},
        )

    await db.commit()
    await db.refresh(tx)

    await publish_event("transaction.created", str(tx.id), {
        "event": "transaction.payment",
        "transaction_id": str(tx.id),
        "account_id": str(payload.account_id),
        "amount": float(payload.amount),
        "merchant": payload.merchant,
        "status": tx.status,
    })

    return tx


@router.get("", response_model=TransactionListResponse)
async def get_transactions(
    account_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_account(account_id, current_user["id"], db)

    filters = [Transaction.account_id == account_id]
    if type:
        filters.append(Transaction.type == type)
    if status:
        filters.append(Transaction.status == status)

    count_result = await db.execute(
        select(func.count(Transaction.id)).where(and_(*filters))
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Transaction)
        .where(and_(*filters))
        .order_by(Transaction.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    transactions = result.scalars().all()

    return TransactionListResponse(total=total, page=page, per_page=per_page, transactions=transactions)


@router.get("/stats/{account_id}", response_model=TransactionStatsResponse)
async def get_stats(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_account(account_id, current_user["id"], db)

    credited = await db.execute(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.account_id == account_id, Transaction.type == "credit", Transaction.status == "completed"))
    debited = await db.execute(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.account_id == account_id, Transaction.type.in_(["debit", "transfer", "payment"]), Transaction.status == "completed"))
    total = await db.execute(select(func.count(Transaction.id)).where(Transaction.account_id == account_id))
    avg = await db.execute(select(func.coalesce(func.avg(Transaction.amount), 0)).where(Transaction.account_id == account_id, Transaction.status == "completed"))
    flagged = await db.execute(select(func.count(Transaction.id)).where(Transaction.account_id == account_id, Transaction.status == "flagged"))

    return TransactionStatsResponse(
        total_credited=credited.scalar(),
        total_debited=debited.scalar(),
        total_transactions=total.scalar(),
        avg_transaction=avg.scalar(),
        flagged_count=flagged.scalar(),
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    return tx


@router.post("/{transaction_id}/reverse")
async def reverse_transaction(
    transaction_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    if tx.status != "completed":
        raise HTTPException(status_code=400, detail="Seules les transactions complétées peuvent être reversées")

    tx.status = "reversed"
    await db.commit()

    await publish_event("transaction.reversed", str(tx.id), {
        "event": "transaction.reversed",
        "transaction_id": str(tx.id),
    })

    return {"message": "Transaction reversée", "transaction_id": str(transaction_id)}
