import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    to_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    risk_score: Mapped[int] = mapped_column(default=0)
    fraud_flags: Mapped[dict] = mapped_column(JSONB, default=list)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    balance_before: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_tx_account_id", "account_id"),
        Index("idx_tx_status", "status"),
        Index("idx_tx_created_at", "created_at"),
        Index("idx_tx_type", "type"),
    )
