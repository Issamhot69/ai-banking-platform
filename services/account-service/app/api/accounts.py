from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.kafka import publish_event
from app.models.account import Account
from app.schemas.account import (
    CreateAccountRequest, AccountResponse,
    UpdateLimitsRequest, FreezeAccountRequest, AccountSummaryResponse,
)
from app.utils.iban import generate_account_number, generate_iban
from app.utils.dependencies import get_current_user
from app.websockets.manager import manager

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    payload: CreateAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_number = generate_account_number()
    iban = generate_iban(account_number=account_number)

    account = Account(
        user_id=current_user["id"],
        account_number=account_number,
        iban=iban,
        account_type=payload.account_type,
        currency=payload.currency,
        is_primary=payload.is_primary,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    await publish_event(
        topic="account.created",
        key=str(account.id),
        payload={
            "event": "account.created",
            "account_id": str(account.id),
            "user_id": str(account.user_id),
            "account_type": account.account_type,
            "currency": account.currency,
        },
    )

    await manager.send_to_user(
        str(current_user["id"]),
        {"type": "account.created", "account_id": str(account.id), "currency": account.currency},
    )

    return account


@router.get("", response_model=AccountSummaryResponse)
async def get_my_accounts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(Account.user_id == current_user["id"])
    )
    accounts = result.scalars().all()
    total_balance = sum(a.balance for a in accounts if a.currency == "EUR")
    currencies = list(set(a.currency for a in accounts))

    return AccountSummaryResponse(
        total_accounts=len(accounts),
        total_balance=total_balance,
        currencies=currencies,
        accounts=accounts,
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user["id"],
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return account


@router.post("/{account_id}/freeze")
async def freeze_account(
    account_id: uuid.UUID,
    payload: FreezeAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user["id"],
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    account.status = "frozen"
    await db.commit()

    await publish_event(
        topic="account.frozen",
        key=str(account.id),
        payload={"event": "account.frozen", "account_id": str(account.id), "reason": payload.reason},
    )
    return {"message": "Compte gelé avec succès", "account_id": str(account_id)}


@router.post("/{account_id}/unfreeze")
async def unfreeze_account(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user["id"],
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    account.status = "active"
    await db.commit()
    return {"message": "Compte dégelé avec succès"}


@router.patch("/{account_id}/limits")
async def update_limits(
    account_id: uuid.UUID,
    payload: UpdateLimitsRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user["id"],
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    if payload.daily_transfer_limit:
        account.daily_transfer_limit = payload.daily_transfer_limit
    if payload.monthly_transfer_limit:
        account.monthly_transfer_limit = payload.monthly_transfer_limit

    await db.commit()
    return {"message": "Limites mises à jour", "account_id": str(account_id)}


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
