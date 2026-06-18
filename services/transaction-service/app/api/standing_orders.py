import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.standing_order import StandingOrder
from app.schemas.standing_order import StandingOrderCreate, StandingOrderResponse, StandingOrderListResponse
from app.utils.dependencies import get_current_user
from app.api.transactions import _get_account, _get_account_any

router = APIRouter()


@router.post("", response_model=StandingOrderResponse, status_code=201)
async def create_standing_order(
    payload: StandingOrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_account(payload.from_account_id, current_user["id"], db)
    await _get_account_any(payload.to_account_id, db)

    order = StandingOrder(
        user_id=current_user["id"],
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        currency=payload.currency,
        frequency=payload.frequency,
        description=payload.description,
        next_execution_date=datetime.now(timezone.utc),
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.get("", response_model=StandingOrderListResponse)
async def list_standing_orders(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StandingOrder).where(StandingOrder.user_id == uuid.UUID(current_user["id"]))
        .order_by(StandingOrder.created_at.desc())
    )
    orders = result.scalars().all()
    return {"standing_orders": orders}


async def _get_owned_order(order_id: uuid.UUID, current_user: dict, db: AsyncSession) -> StandingOrder:
    result = await db.execute(select(StandingOrder).where(StandingOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Ordre permanent introuvable")
    if str(order.user_id) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return order


@router.delete("/{order_id}", response_model=StandingOrderResponse)
async def cancel_standing_order(
    order_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_owned_order(order_id, current_user, db)
    order.status = "cancelled"
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/pause", response_model=StandingOrderResponse)
async def pause_standing_order(
    order_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_owned_order(order_id, current_user, db)
    if order.status != "active":
        raise HTTPException(status_code=400, detail="Seul un ordre actif peut être mis en pause")
    order.status = "paused"
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/resume", response_model=StandingOrderResponse)
async def resume_standing_order(
    order_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_owned_order(order_id, current_user, db)
    if order.status != "paused":
        raise HTTPException(status_code=400, detail="Seul un ordre en pause peut être repris")
    order.status = "active"
    await db.commit()
    await db.refresh(order)
    return order
