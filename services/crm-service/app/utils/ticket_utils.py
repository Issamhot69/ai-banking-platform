import random
import string
from datetime import datetime, timezone

def generate_ticket_number() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"TKT-{timestamp}-{random_part}"

SEGMENT_THRESHOLDS = {
    "vip": 50000,
    "premium": 10000,
    "standard": 0,
}

def determine_segment(lifetime_value: float) -> str:
    if lifetime_value >= SEGMENT_THRESHOLDS["vip"]:
        return "vip"
    elif lifetime_value >= SEGMENT_THRESHOLDS["premium"]:
        return "premium"
    return "standard"
