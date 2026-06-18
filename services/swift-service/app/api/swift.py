from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, desc
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.models.swift import SWIFTTransfer
from app.schemas.swift import SWIFTTransferRequest, SWIFTTransferResponse, ExchangeRateResponse
from app.utils.dependencies import get_current_user
from app.utils.swift_utils import (
    generate_swift_reference, convert_to_eur, calculate_fee,
    get_processing_time, check_aml, get_exchange_rate
)

router = APIRouter(prefix="/swift", tags=["SWIFT Transfers"])


@router.get("/rates", response_model=dict)
async def get_exchange_rates():
    from app.utils.swift_utils import EXCHANGE_RATES, RATES_LAST_UPDATED, RATES_SOURCE
    return {
        "source": RATES_SOURCE,
        "last_updated": RATES_LAST_UPDATED.isoformat() if RATES_LAST_UPDATED else None,
        "rates": [
            {"currency": currency, "rate_to_eur": str(rate)}
            for currency, rate in EXCHANGE_RATES.items()
        ],
    }


@router.get("/rates/convert", response_model=ExchangeRateResponse)
async def convert_currency(
    amount: Decimal,
    from_currency: str,
    to_currency: str = "EUR",
    current_user: dict = Depends(get_current_user),
):
    amount_eur = convert_to_eur(amount, from_currency.upper())
    fee = calculate_fee(amount_eur)
    rate = get_exchange_rate(from_currency.upper(), to_currency.upper())

    return ExchangeRateResponse(
        from_currency=from_currency.upper(),
        to_currency=to_currency.upper(),
        rate=rate,
        amount=amount,
        converted_amount=amount_eur,
        fee=fee,
        total=amount_eur + fee,
    )


@router.post("/transfer", response_model=SWIFTTransferResponse, status_code=201)
async def create_swift_transfer(
    payload: SWIFTTransferRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier le compte source
    account = await db.execute(
        text("SELECT id, balance, available_balance, currency FROM accounts WHERE id = :id AND user_id = :uid AND status = 'active'"),
        {"id": str(payload.from_account_id), "uid": current_user["id"]}
    )
    acc = account.mappings().first()
    if not acc:
        raise HTTPException(status_code=404, detail="Compte introuvable ou inactif")

    # Conversion et frais
    amount_eur = convert_to_eur(payload.amount, payload.currency)
    fee = calculate_fee(amount_eur)
    total_deducted = amount_eur + fee
    exchange_rate = get_exchange_rate(payload.currency)

    # Vérifier le solde
    if Decimal(str(acc["available_balance"])) < total_deducted:
        raise HTTPException(
            status_code=400,
            detail=f"Solde insuffisant. Requis: {total_deducted} EUR (montant: {amount_eur} EUR + frais: {fee} EUR)"
        )

    # Vérification AML
    aml_result = check_aml(amount_eur, payload.beneficiary_country, payload.beneficiary_name)

    if aml_result["status"] == "blocked":
        raise HTTPException(
            status_code=403,
            detail=f"Transfert bloqué par conformité AML. Flags: {', '.join(aml_result['flags'])}"
        )

    # Créer le transfert
    transfer = SWIFTTransfer(
        reference=generate_swift_reference(),
        user_id=current_user["id"],
        from_account_id=payload.from_account_id,
        sender_name=payload.sender_name,
        sender_address=payload.sender_address,
        sender_country=payload.sender_country,
        beneficiary_name=payload.beneficiary_name,
        beneficiary_address=payload.beneficiary_address,
        beneficiary_country=payload.beneficiary_country,
        beneficiary_account=payload.beneficiary_account,
        beneficiary_bank_name=payload.beneficiary_bank_name,
        beneficiary_bic=payload.beneficiary_bic,
        amount=payload.amount,
        currency=payload.currency,
        exchange_rate=exchange_rate,
        amount_in_eur=amount_eur,
        fee=fee,
        total_deducted=total_deducted,
        purpose_code=payload.purpose_code,
        remittance_info=payload.remittance_info,
        status="processing",
        aml_status=aml_result["status"],
        aml_flags=aml_result,
        estimated_arrival=get_processing_time(payload.beneficiary_country),
        processed_at=datetime.now(timezone.utc),
    )

    db.add(transfer)

    # Débiter le compte
    await db.execute(
        text("UPDATE accounts SET balance = balance - :amount, available_balance = available_balance - :amount WHERE id = :id"),
        {"amount": float(total_deducted), "id": str(payload.from_account_id)}
    )

    await db.commit()
    await db.refresh(transfer)

    # Simuler le traitement (status → completed)
    transfer.status = "completed"
    await db.commit()
    await db.refresh(transfer)

    return transfer


@router.get("/transfers", response_model=list[SWIFTTransferResponse])
async def get_my_transfers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SWIFTTransfer)
        .where(SWIFTTransfer.user_id == current_user["id"])
        .order_by(desc(SWIFTTransfer.created_at))
    )
    return result.scalars().all()


@router.get("/transfers/{transfer_id}", response_model=SWIFTTransferResponse)
async def get_transfer(
    transfer_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SWIFTTransfer).where(
            SWIFTTransfer.id == transfer_id,
            SWIFTTransfer.user_id == current_user["id"]
        )
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfert introuvable")
    return transfer


@router.get("/validate/bic/{bic}")
async def validate_bic(bic: str, current_user: dict = Depends(get_current_user)):
    bic = bic.upper().strip()
    if len(bic) not in [8, 11]:
        return {"valid": False, "error": "BIC doit avoir 8 ou 11 caractères"}

    bank_code = bic[:4]
    country_code = bic[4:6]
    location_code = bic[6:8]
    branch_code = bic[8:] if len(bic) == 11 else "XXX"

    return {
        "valid": True,
        "bic": bic,
        "bank_code": bank_code,
        "country_code": country_code,
        "location_code": location_code,
        "branch_code": branch_code,
    }
