import random
import hashlib
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


def generate_card_number(card_type: str = "visa") -> str:
    if card_type == "visa":
        prefix = "4"
    elif card_type == "mastercard":
        prefix = "5" + str(random.randint(1, 5))
    else:
        prefix = "4"

    number = prefix
    while len(number) < 15:
        number += str(random.randint(0, 9))

    # Luhn algorithm check digit
    digits = [int(d) for d in number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    check = (10 - (total % 10)) % 10
    number += str(check)

    # Format: 4111 1111 1111 1111
    return " ".join([number[i:i+4] for i in range(0, 16, 4)])


def mask_card_number(card_number: str) -> str:
    clean = card_number.replace(" ", "")
    return f"**** **** **** {clean[-4:]}"


def generate_cvv() -> str:
    return str(random.randint(100, 999))


def hash_cvv(cvv: str) -> str:
    return hashlib.sha256(cvv.encode()).hexdigest()


def get_expiry_date():
    future = datetime.now(timezone.utc) + relativedelta(years=3)
    return future.month, future.year
