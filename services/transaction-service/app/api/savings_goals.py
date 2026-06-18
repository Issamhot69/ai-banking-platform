import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.savings_goal import SavingsGoal
from app.schemas.savings_goal import SavingsGoalCreate, SavingsGoalResponse, SavingsGoalListResponse
from app.utils.dependencies import get_current_user
from app.api.transactions import _get_account, _get_account_any

router = APIRouter()


@router.post("", response_model=SavingsGoalResponse, status_code=201)
async def create_savings_goal(
    payload: SavingsGoalCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_account(payload.source_account_id, current_user["id"], db)
    await _get_account(payload.goal_account_id, current_user["id"], db)

    if str(payload.source_account_id) == str(payload.goal_account_id):
        raise HTTPException(status_code=400, detail="Le compte source et le compte objectif doivent être différents")

    goal = SavingsGoal(
        user_id=current_user["id"],
        goal_account_id=payload.goal_account_id,
        source_account_id=payload.source_account_id,
        name=payload.name,
        target_amount=payload.target_amount,
        round_up_enabled=payload.round_up_enabled,
        round_up_multiple=payload.round_up_multiple,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("", response_model=SavingsGoalListResponse)
async def list_savings_goals(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavingsGoal).where(SavingsGoal.user_id == uuid.UUID(current_user["id"]))
        .order_by(SavingsGoal.created_at.desc())
    )
    goals = result.scalars().all()
    return {"savings_goals": goals}


async def _get_owned_goal(goal_id: uuid.UUID, current_user: dict, db: AsyncSession) -> SavingsGoal:
    result = await db.execute(select(SavingsGoal).where(SavingsGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Objectif d'épargne introuvable")
    if str(goal.user_id) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return goal


@router.post("/{goal_id}/pause", response_model=SavingsGoalResponse)
async def pause_savings_goal(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await _get_owned_goal(goal_id, current_user, db)
    goal.status = "paused"
    goal.round_up_enabled = False
    await db.commit()
    await db.refresh(goal)
    return goal


@router.post("/{goal_id}/resume", response_model=SavingsGoalResponse)
async def resume_savings_goal(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await _get_owned_goal(goal_id, current_user, db)
    goal.status = "active"
    goal.round_up_enabled = True
    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", response_model=SavingsGoalResponse)
async def cancel_savings_goal(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await _get_owned_goal(goal_id, current_user, db)
    goal.status = "cancelled"
    goal.round_up_enabled = False
    await db.commit()
    await db.refresh(goal)
    return goal
