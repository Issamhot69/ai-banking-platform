from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.models.crm import CustomerProfile, SupportTicket, CustomerInteraction
from app.schemas.crm import (
    CustomerProfileCreate, CustomerProfileUpdate, CustomerProfileResponse,
    TicketCreate, TicketUpdate, TicketResponse,
    InteractionCreate, InteractionResponse, CRMStatsResponse
)
from app.utils.dependencies import get_current_user
from app.utils.ticket_utils import generate_ticket_number, determine_segment

router = APIRouter(prefix="/crm", tags=["CRM"])


@router.post("/customers", response_model=CustomerProfileResponse, status_code=201)
async def create_customer_profile(
    payload: CustomerProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(CustomerProfile).where(CustomerProfile.user_id == payload.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Profil CRM déjà existant")

    profile = CustomerProfile(**payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/customers", response_model=list[CustomerProfileResponse])
async def get_all_customers(
    segment: str = None,
    is_vip: bool = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CustomerProfile).order_by(desc(CustomerProfile.created_at))
    if segment:
        query = query.where(CustomerProfile.segment == segment)
    if is_vip is not None:
        query = query.where(CustomerProfile.is_vip == is_vip)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/customers/{user_id}", response_model=CustomerProfileResponse)
async def get_customer_profile(
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CustomerProfile).where(CustomerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil CRM introuvable")
    return profile


@router.patch("/customers/{user_id}", response_model=CustomerProfileResponse)
async def update_customer_profile(
    user_id: uuid.UUID,
    payload: CustomerProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CustomerProfile).where(CustomerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(
    payload: TicketCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = SupportTicket(
        user_id=current_user["id"],
        ticket_number=generate_ticket_number(),
        **payload.model_dump(),
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=list[TicketResponse])
async def get_tickets(
    status: str = None,
    priority: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SupportTicket).order_by(desc(SupportTicket.created_at))
    if status:
        query = query.where(SupportTicket.status == status)
    if priority:
        query = query.where(SupportTicket.priority == priority)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(ticket, field, value)

    if payload.status == "resolved":
        ticket.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/customers/{user_id}/interactions", response_model=InteractionResponse, status_code=201)
async def add_interaction(
    user_id: uuid.UUID,
    payload: InteractionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    interaction = CustomerInteraction(user_id=user_id, **payload.model_dump())
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


@router.get("/customers/{user_id}/interactions", response_model=list[InteractionResponse])
async def get_interactions(
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CustomerInteraction)
        .where(CustomerInteraction.user_id == user_id)
        .order_by(desc(CustomerInteraction.created_at))
    )
    return result.scalars().all()


@router.get("/stats", response_model=CRMStatsResponse)
async def get_crm_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(CustomerProfile.id)))).scalar() or 0
    vip = (await db.execute(select(func.count(CustomerProfile.id)).where(CustomerProfile.is_vip == True))).scalar() or 0
    open_tickets = (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status == "open"))).scalar() or 0
    resolved = (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status == "resolved"))).scalar() or 0
    avg_sat = (await db.execute(select(func.avg(CustomerProfile.satisfaction_score)))).scalar() or 0.0

    seg_result = await db.execute(
        select(CustomerProfile.segment, func.count(CustomerProfile.id)).group_by(CustomerProfile.segment)
    )
    by_segment = {row[0]: row[1] for row in seg_result.fetchall()}

    return CRMStatsResponse(
        total_customers=total,
        vip_customers=vip,
        open_tickets=open_tickets,
        resolved_tickets=resolved,
        by_segment=by_segment,
        avg_satisfaction=float(avg_sat),
    )
