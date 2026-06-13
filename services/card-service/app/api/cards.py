from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import uuid

from app.core.database import get_db
from app.models.card import VirtualCard
from app.schemas.card import CreateCardRequest, CardResponse, CardDetailsResponse, UpdateCardRequest
from app.utils.dependencies import get_current_user
from app.utils.card_generator import generate_card_number, mask_card_number, generate_cvv, hash_cvv, get_expiry_date

router = APIRouter(prefix="/cards", tags=["Virtual Cards"])


@router.post("", response_model=CardDetailsResponse, status_code=201)
async def create_card(
    payload: CreateCardRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier que le compte appartient à l'utilisateur
    result = await db.execute(
        text("SELECT id FROM accounts WHERE id = :id AND user_id = :uid AND status = 'active'"),
        {"id": str(payload.account_id), "uid": current_user["id"]}
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Compte introuvable ou inactif")

    # Générer les données de la carte
    card_number = generate_card_number(payload.card_type)
    cvv = generate_cvv()
    expiry_month, expiry_year = get_expiry_date()

    card = VirtualCard(
        user_id=current_user["id"],
        account_id=payload.account_id,
        card_number=card_number,
        card_number_masked=mask_card_number(card_number),
        card_holder_name=payload.card_holder_name.upper(),
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        cvv_hash=hash_cvv(cvv),
        card_type=payload.card_type,
        daily_limit=payload.daily_limit,
        monthly_limit=payload.monthly_limit,
    )

    db.add(card)
    await db.commit()
    await db.refresh(card)

    response = CardDetailsResponse.model_validate(card)
    response.card_number = card_number
    response.cvv = cvv
    return response


@router.get("", response_model=list[CardResponse])
async def get_my_cards(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VirtualCard).where(VirtualCard.user_id == current_user["id"])
    )
    return result.scalars().all()


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VirtualCard).where(
            VirtualCard.id == card_id,
            VirtualCard.user_id == current_user["id"]
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    return card


@router.patch("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: uuid.UUID,
    payload: UpdateCardRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VirtualCard).where(
            VirtualCard.id == card_id,
            VirtualCard.user_id == current_user["id"]
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")

    if payload.daily_limit is not None:
        card.daily_limit = payload.daily_limit
    if payload.monthly_limit is not None:
        card.monthly_limit = payload.monthly_limit
    if payload.is_online_enabled is not None:
        card.is_online_enabled = payload.is_online_enabled
    if payload.is_international_enabled is not None:
        card.is_international_enabled = payload.is_international_enabled
    if payload.is_contactless is not None:
        card.is_contactless = payload.is_contactless

    await db.commit()
    await db.refresh(card)
    return card


@router.post("/{card_id}/freeze", response_model=CardResponse)
async def freeze_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VirtualCard).where(
            VirtualCard.id == card_id,
            VirtualCard.user_id == current_user["id"]
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    card.status = "frozen"
    await db.commit()
    await db.refresh(card)
    return card


@router.post("/{card_id}/unfreeze", response_model=CardResponse)
async def unfreeze_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VirtualCard).where(
            VirtualCard.id == card_id,
            VirtualCard.user_id == current_user["id"]
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    card.status = "active"
    await db.commit()
    await db.refresh(card)
    return card


@router.delete("/{card_id}")
async def cancel_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VirtualCard).where(
            VirtualCard.id == card_id,
            VirtualCard.user_id == current_user["id"]
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    card.status = "cancelled"
    await db.commit()
    return {"message": "Carte annulée", "card_id": str(card_id)}
