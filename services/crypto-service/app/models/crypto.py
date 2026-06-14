import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Boolean, Index, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Table, Column
from app.core.database import Base

users_table = Table("users", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), extend_existing=True)

class CryptoWallet(Base):
    __tablename__ = "crypto_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    address: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=Decimal("0.0"))
    balance_eur: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_wallet_user_id", "user_id"),
        Index("idx_wallet_currency", "currency"),
    )


class CryptoTransaction(Base):
    __tablename__ = "crypto_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crypto_wallets.id"), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tx_type: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=Decimal("0.0"))
    fee_eur: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.0"))
    from_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_at_tx: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    network_confirmations: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_crypto_tx_user_id", "user_id"),
        Index("idx_crypto_tx_wallet_id", "wallet_id"),
        Index("idx_crypto_tx_hash", "tx_hash"),
    )
