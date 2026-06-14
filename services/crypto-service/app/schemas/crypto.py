from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid

class CreateWalletRequest(BaseModel):
    currency: str

class WalletResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    currency: str
    address: str
    balance: Decimal
    balance_eur: Decimal
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class CryptoTransactionRequest(BaseModel):
    wallet_id: uuid.UUID
    tx_type: str  # buy, sell, send, receive
    amount: Decimal
    to_address: Optional[str] = None
    description: Optional[str] = None

class CryptoTransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    wallet_id: uuid.UUID
    tx_hash: str
    tx_type: str
    currency: str
    amount: Decimal
    amount_eur: Decimal
    fee: Decimal
    fee_eur: Decimal
    from_address: Optional[str]
    to_address: Optional[str]
    price_at_tx: Decimal
    status: str
    network_confirmations: int
    description: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class CryptoPriceResponse(BaseModel):
    currency: str
    price_eur: Decimal
    price_usd: Decimal
    change_24h: Decimal
    market_cap_eur: Optional[Decimal]

class PortfolioResponse(BaseModel):
    total_value_eur: Decimal
    wallets: List[WalletResponse]
    performance_24h: Decimal
