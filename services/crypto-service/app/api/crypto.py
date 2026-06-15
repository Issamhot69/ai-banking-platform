from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.models.crypto import CryptoWallet, CryptoTransaction
from app.schemas.crypto import (
    CreateWalletRequest, WalletResponse, CryptoTransactionRequest,
    CryptoTransactionResponse, CryptoPriceResponse, PortfolioResponse
)
from app.utils.dependencies import get_current_user
from app.utils.crypto_utils import (
    generate_wallet_address, generate_tx_hash,
    get_price_eur, convert_to_eur, convert_eur_to_crypto,
    calculate_fee, CRYPTO_PRICES_EUR, CHANGE_24H
)
from app.core.config import settings

router = APIRouter(prefix="/crypto", tags=["Crypto Wallet"])


@router.get("/prices", response_model=list[CryptoPriceResponse])
async def get_prices(current_user: dict = Depends(get_current_user)):
    prices = []
    for currency, price_eur in CRYPTO_PRICES_EUR.items():
        prices.append(CryptoPriceResponse(
            currency=currency,
            price_eur=get_price_eur(currency),
            price_usd=(get_price_eur(currency) * Decimal("1.09")).quantize(Decimal("0.01")),
            change_24h=CHANGE_24H.get(currency, Decimal("0")),
            market_cap_eur=None,
        ))
    return prices


@router.get("/prices/{currency}", response_model=CryptoPriceResponse)
async def get_price(currency: str, current_user: dict = Depends(get_current_user)):
    currency = currency.upper()
    if currency not in CRYPTO_PRICES_EUR:
        raise HTTPException(status_code=404, detail=f"Crypto {currency} non supportée")
    return CryptoPriceResponse(
        currency=currency,
        price_eur=get_price_eur(currency),
        price_usd=(get_price_eur(currency) * Decimal("1.09")).quantize(Decimal("0.01")),
        change_24h=CHANGE_24H.get(currency, Decimal("0")),
        market_cap_eur=None,
    )


@router.post("/wallets", response_model=WalletResponse, status_code=201)
async def create_wallet(
    payload: CreateWalletRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    currency = payload.currency.upper()
    if currency not in settings.SUPPORTED_CRYPTOS:
        raise HTTPException(status_code=400, detail=f"Crypto non supportée. Supportées: {', '.join(settings.SUPPORTED_CRYPTOS)}")

    existing = await db.execute(
        select(CryptoWallet).where(
            CryptoWallet.user_id == current_user["id"],
            CryptoWallet.currency == currency,
            CryptoWallet.is_active == True
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Wallet {currency} existe déjà")

    wallet = CryptoWallet(
        user_id=current_user["id"],
        currency=currency,
        address=generate_wallet_address(currency),
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


@router.get("/wallets", response_model=list[WalletResponse])
async def get_wallets(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CryptoWallet).where(CryptoWallet.user_id == current_user["id"])
    )
    return result.scalars().all()


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CryptoWallet).where(CryptoWallet.user_id == current_user["id"])
    )
    wallets = result.scalars().all()

    total_value = Decimal("0")
    for w in wallets:
        w.balance_eur = convert_to_eur(w.balance, w.currency)
        total_value += w.balance_eur

    return PortfolioResponse(
        total_value_eur=total_value,
        wallets=wallets,
        performance_24h=Decimal("2.35"),
    )


@router.post("/transactions", response_model=CryptoTransactionResponse, status_code=201)
async def create_transaction(
    payload: CryptoTransactionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet_result = await db.execute(
        select(CryptoWallet).where(
            CryptoWallet.id == payload.wallet_id,
            CryptoWallet.user_id == current_user["id"]
        )
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet introuvable")

    price_eur = get_price_eur(wallet.currency)
    fee_crypto = (payload.amount * Decimal("0.005")).quantize(Decimal("0.00000001"))
    fee_eur = (fee_crypto * price_eur).quantize(Decimal("0.01"))
    amount_eur = convert_to_eur(payload.amount, wallet.currency)

    if payload.tx_type == "buy":
        crypto_amount = convert_eur_to_crypto(payload.amount, wallet.currency)
        wallet.balance += crypto_amount
        wallet.balance_eur = convert_to_eur(wallet.balance, wallet.currency)
        amount_eur = payload.amount
        tx_amount = crypto_amount
    elif payload.tx_type == "sell":
        if wallet.balance < payload.amount:
            raise HTTPException(status_code=400, detail="Solde crypto insuffisant")
        wallet.balance -= payload.amount
        wallet.balance_eur = convert_to_eur(wallet.balance, wallet.currency)
        tx_amount = payload.amount
    elif payload.tx_type == "send":
        if not payload.to_address:
            raise HTTPException(status_code=400, detail="Adresse destinataire requise")
        total_needed = payload.amount + fee_crypto
        if wallet.balance < total_needed:
            raise HTTPException(status_code=400, detail="Solde insuffisant (montant + frais)")
        wallet.balance -= total_needed
        wallet.balance_eur = convert_to_eur(wallet.balance, wallet.currency)
        tx_amount = payload.amount
    else:
        raise HTTPException(status_code=400, detail="Type invalide: buy, sell, send")

    tx = CryptoTransaction(
        user_id=current_user["id"],
        wallet_id=wallet.id,
        tx_hash=generate_tx_hash(),
        tx_type=payload.tx_type,
        currency=wallet.currency,
        amount=tx_amount,
        amount_eur=amount_eur,
        fee=fee_crypto,
        fee_eur=fee_eur,
        from_address=wallet.address,
        to_address=payload.to_address,
        price_at_tx=price_eur,
        status="completed",
        network_confirmations=6,
        description=payload.description,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


@router.get("/transactions", response_model=list[CryptoTransactionResponse])
async def get_transactions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CryptoTransaction)
        .where(CryptoTransaction.user_id == current_user["id"])
        .order_by(desc(CryptoTransaction.created_at))
        .limit(50)
    )
    return result.scalars().all()
