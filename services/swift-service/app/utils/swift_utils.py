import random
import string
import logging
import httpx
from decimal import Decimal
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger(__name__)

# Taux de secours (utilisés si l'API externe est indisponible)
EXCHANGE_RATES = {
    "EUR": Decimal("1.0"),
    "USD": Decimal("0.92"),
    "GBP": Decimal("1.17"),
    "MAD": Decimal("0.091"),
    "CHF": Decimal("1.03"),
    "JPY": Decimal("0.0061"),
    "CAD": Decimal("0.68"),
    "AUD": Decimal("0.60"),
    "AED": Decimal("0.25"),
}

RATES_LAST_UPDATED: datetime | None = None
RATES_SOURCE = "fallback_static"

FRANKFURTER_URL = "https://api.frankfurter.dev/v2/rates"


async def refresh_exchange_rates() -> bool:
    """Récupère les taux de change réels (BCE, via Frankfurter) et met à jour le cache en mémoire.
    L'API renvoie une liste d'enregistrements {date, base, quote, rate} potentiellement sur
    plusieurs dates — on ne garde que le taux le plus récent par devise.
    En cas d'échec, conserve les derniers taux connus (statiques ou précédemment récupérés)."""
    global RATES_LAST_UPDATED, RATES_SOURCE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(FRANKFURTER_URL, params={"base": "EUR"})
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list):
            raise ValueError(f"Format de réponse inattendu: {type(data)}")

        latest_date_per_currency: dict[str, str] = {}
        rate_per_currency: dict[str, Decimal] = {}

        for record in data:
            quote = record.get("quote")
            date = record.get("date")
            rate = record.get("rate")
            if not quote or date is None or rate is None:
                continue
            if quote not in latest_date_per_currency or date > latest_date_per_currency[quote]:
                latest_date_per_currency[quote] = date
                rate_per_currency[quote] = Decimal(str(rate))

        if not rate_per_currency:
            raise ValueError("Aucun taux exploitable dans la réponse")

        EXCHANGE_RATES["EUR"] = Decimal("1.0")
        for currency, rate in rate_per_currency.items():
            EXCHANGE_RATES[currency] = rate

        RATES_LAST_UPDATED = datetime.now(timezone.utc)
        RATES_SOURCE = "frankfurter_ecb_live"
        logger.info(f"Taux de change actualisés depuis Frankfurter ({len(rate_per_currency)} devises)")
        return True
    except Exception as e:
        logger.warning(f"Échec de récupération des taux en direct, conservation des taux de secours: {e}")
        return False

# Temps de traitement estimé par pays
PROCESSING_TIMES = {
    "US": "1-2 business days",
    "GB": "1 business day",
    "FR": "1 business day",
    "DE": "1 business day",
    "JP": "2-3 business days",
    "MA": "Same day",
    "DEFAULT": "2-5 business days",
}

def generate_swift_reference() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SWIFT-{timestamp}-{random_part}"

def get_exchange_rate(from_currency: str, to_currency: str = "EUR") -> Decimal:
    from_rate = EXCHANGE_RATES.get(from_currency, Decimal("1.0"))
    to_rate = EXCHANGE_RATES.get(to_currency, Decimal("1.0"))
    return from_rate / to_rate

def convert_to_eur(amount: Decimal, currency: str) -> Decimal:
    if currency == "EUR":
        return amount
    rate = EXCHANGE_RATES.get(currency, Decimal("1.0"))
    return (amount * rate).quantize(Decimal("0.01"))

def calculate_fee(amount_eur: Decimal) -> Decimal:
    fee = amount_eur * Decimal(str(settings.SWIFT_FEE_PERCENTAGE / 100))
    fee = max(fee, Decimal(str(settings.SWIFT_MIN_FEE)))
    fee = min(fee, Decimal(str(settings.SWIFT_MAX_FEE)))
    return fee.quantize(Decimal("0.01"))

def get_processing_time(country: str) -> str:
    return PROCESSING_TIMES.get(country.upper(), PROCESSING_TIMES["DEFAULT"])

def check_aml(amount_eur: Decimal, beneficiary_country: str, beneficiary_name: str) -> dict:
    flags = []
    risk_score = 0

    # Montant élevé
    if amount_eur > Decimal("10000"):
        flags.append("high_value_transfer")
        risk_score += 30

    # Pays à risque (liste simplifiée)
    high_risk_countries = ["KP", "IR", "SY", "CU"]
    if beneficiary_country.upper() in high_risk_countries:
        flags.append("high_risk_country")
        risk_score += 70

    # Noms suspects (liste simplifiée)
    if any(word in beneficiary_name.upper() for word in ["UNKNOWN", "ANONYMOUS"]):
        flags.append("suspicious_beneficiary")
        risk_score += 50

    return {
        "risk_score": risk_score,
        "flags": flags,
        "status": "blocked" if risk_score >= 70 else "cleared",
    }
