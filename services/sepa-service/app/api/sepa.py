from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, desc
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.models.sepa import SEPATransfer
from app.schemas.sepa import SEPATransferRequest, SEPATransferResponse
from app.utils.dependencies import get_current_user
from app.utils.sepa_utils import (
    generate_sepa_reference, generate_end_to_end_id,
    extract_country_from_iban, is_sepa_country,
    get_settlement_date, validate_sepa_iban
)
from app.core.config import settings

router = APIRouter(prefix="/sepa", tags=["SEPA Transfers"])


@router.get("/countries")
async def get_sepa_countries():
    from app.utils.sepa_utils import SEPA_COUNTRIES
    return {"sepa_countries": SEPA_COUNTRIES, "total": len(SEPA_COUNTRIES)}


@router.get("/validate/iban/{iban}")
async def validate_iban(iban: str, current_user: dict = Depends(get_current_user)):
    return validate_sepa_iban(iban)


@router.post("/transfer", response_model=SEPATransferResponse, status_code=201)
async def create_sepa_transfer(
    payload: SEPATransferRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Valider IBAN destinataire
    iban_validation = validate_sepa_iban(payload.creditor_iban)
    if not iban_validation["valid"]:
        raise HTTPException(status_code=400, detail=f"IBAN invalide: {iban_validation['error']}")

    creditor_country = extract_country_from_iban(payload.creditor_iban)

    # Vérifier montant instant
    if payload.is_instant and payload.amount > Decimal(str(settings.SEPA_MAX_AMOUNT_INSTANT)):
        raise HTTPException(
            status_code=400,
            detail=f"Montant maximum pour virement instantané: {settings.SEPA_MAX_AMOUNT_INSTANT} EUR"
        )

    # Vérifier compte source
    account = await db.execute(
        text("SELECT id, balance, available_balance, iban FROM accounts WHERE id = :id AND user_id = :uid AND status = 'active'"),
        {"id": str(payload.from_account_id), "uid": current_user["id"]}
    )
    acc = account.mappings().first()
    if not acc:
        raise HTTPException(status_code=404, detail="Compte introuvable ou inactif")

    # Calculer frais
    fee = Decimal(str(settings.SEPA_FEE_INSTANT if payload.is_instant else settings.SEPA_FEE_STANDARD))
    total = payload.amount + fee

    # Vérifier solde
    if Decimal(str(acc["available_balance"])) < total:
        raise HTTPException(
            status_code=400,
            detail=f"Solde insuffisant. Requis: {total} EUR (montant: {payload.amount} EUR + frais: {fee} EUR)"
        )

    # Créer le transfert
    transfer = SEPATransfer(
        reference=generate_sepa_reference(),
        end_to_end_id=generate_end_to_end_id(),
        user_id=current_user["id"],
        from_account_id=payload.from_account_id,
        debtor_name=payload.debtor_name,
        debtor_iban=payload.debtor_iban,
        debtor_bic=settings.BANK_BIC,
        creditor_name=payload.creditor_name,
        creditor_iban=payload.creditor_iban,
        creditor_bic=payload.creditor_bic,
        creditor_country=creditor_country,
        amount=payload.amount,
        currency="EUR",
        fee=fee,
        transfer_type="SCT Inst" if payload.is_instant else "SCT",
        is_instant=payload.is_instant,
        remittance_info=payload.remittance_info,
        purpose_code=payload.purpose_code,
        status="completed" if payload.is_instant else "processing",
        processed_at=datetime.now(timezone.utc),
        settlement_date=get_settlement_date(payload.is_instant),
    )

    db.add(transfer)

    # Débiter le compte
    await db.execute(
        text("UPDATE accounts SET balance = balance - :amount, available_balance = available_balance - :amount WHERE id = :id"),
        {"amount": float(total), "id": str(payload.from_account_id)}
    )

    await db.commit()
    await db.refresh(transfer)

    # Si standard → processing → completed
    if not payload.is_instant:
        transfer.status = "completed"
        await db.commit()
        await db.refresh(transfer)

    return transfer


@router.get("/transfers", response_model=list[SEPATransferResponse])
async def get_my_transfers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SEPATransfer)
        .where(SEPATransfer.user_id == current_user["id"])
        .order_by(desc(SEPATransfer.created_at))
    )
    return result.scalars().all()


@router.get("/transfers/{transfer_id}", response_model=SEPATransferResponse)
async def get_transfer(
    transfer_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SEPATransfer).where(
            SEPATransfer.id == transfer_id,
            SEPATransfer.user_id == current_user["id"]
        )
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfert introuvable")
    return transfer
