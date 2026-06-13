import random
import string
from datetime import datetime, timezone, timedelta

# Pays SEPA
SEPA_COUNTRIES = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU",
    "MT", "NL", "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "CH", "GB", "MC", "SM", "VA", "AD", "MA"
]

def generate_sepa_reference() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SEPA-{timestamp}-{random_part}"

def generate_end_to_end_id() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=35))

def extract_country_from_iban(iban: str) -> str:
    return iban[:2].upper()

def is_sepa_country(country_code: str) -> bool:
    return country_code.upper() in SEPA_COUNTRIES

def get_settlement_date(is_instant: bool) -> str:
    now = datetime.now(timezone.utc)
    if is_instant:
        return now.strftime("%Y-%m-%d %H:%M:%S") + " (instantané)"
    next_day = now + timedelta(days=1)
    return next_day.strftime("%Y-%m-%d") + " (J+1)"

def validate_sepa_iban(iban: str) -> dict:
    iban = iban.replace(" ", "").upper()
    country = iban[:2]

    if not is_sepa_country(country):
        return {"valid": False, "error": f"Pays {country} non éligible SEPA"}

    if len(iban) < 15 or len(iban) > 34:
        return {"valid": False, "error": "Longueur IBAN invalide"}

    return {
        "valid": True,
        "iban": iban,
        "country": country,
        "is_sepa": True,
        "formatted": ' '.join(iban[i:i+4] for i in range(0, len(iban), 4))
    }
