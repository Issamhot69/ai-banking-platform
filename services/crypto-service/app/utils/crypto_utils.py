import hashlib
import secrets
import random
from decimal import Decimal
from datetime import datetime, timezone

# Prix simulés (en production: API CoinGecko/Binance)
CRYPTO_PRICES_EUR = {
    "BTC": Decimal("58420.50"),
    "ETH": Decimal("3120.75"),
    "USDT": Decimal("0.92"),
    "BNB": Decimal("385.20"),
    "SOL": Decimal("142.80"),
    "MAD_COIN": Decimal("1.00"),
}

CHANGE_24H = {
    "BTC": Decimal("2.35"),
    "ETH": Decimal("-1.20"),
    "USDT": Decimal("0.01"),
    "BNB": Decimal("3.45"),
    "SOL": Decimal("5.80"),
    "MAD_COIN": Decimal("0.00"),
}

def generate_wallet_address(currency: str) -> str:
    random_bytes = secrets.token_bytes(32)
    hash_val = hashlib.sha256(random_bytes).hexdigest()
    
    if currency == "BTC":
        return "1" + hash_val[:33]
    elif currency == "ETH":
        return "0x" + hash_val[:40]
    elif currency in ["BNB", "USDT"]:
        return "0x" + hash_val[:40]
    elif currency == "SOL":
        return hash_val[:44]
    else:
        return "MAD" + hash_val[:32]

def generate_tx_hash() -> str:
    return "0x" + secrets.token_hex(32)

def get_price_eur(currency: str) -> Decimal:
    base_price = CRYPTO_PRICES_EUR.get(currency, Decimal("1.0"))
    variation = Decimal(str(random.uniform(-0.001, 0.001)))
    return (base_price * (1 + variation)).quantize(Decimal("0.01"))

def convert_to_eur(amount: Decimal, currency: str) -> Decimal:
    price = get_price_eur(currency)
    return (amount * price).quantize(Decimal("0.01"))

def convert_eur_to_crypto(amount_eur: Decimal, currency: str) -> Decimal:
    price = get_price_eur(currency)
    return (amount_eur / price).quantize(Decimal("0.00000001"))

def calculate_fee(amount: Decimal, currency: str) -> tuple:
    fee_crypto = (amount * Decimal("0.005")).quantize(Decimal("0.00000001"))
    price = get_price_eur(currency)
    fee_eur = (fee_crypto * price).quantize(Decimal("0.01"))
    return fee_crypto, fee_eur
