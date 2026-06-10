import uuid


def generate_reference(prefix: str = "TXN") -> str:
    from datetime import datetime, timezone
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"{prefix}-{date_str}-{unique}"
