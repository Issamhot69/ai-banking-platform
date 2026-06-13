import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Table, Column
from app.core.database import Base

users_table = Table(
    "users", Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    extend_existing=True,
)

accounts_table = Table(
    "accounts", Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True)),
    extend_existing=True,
)

class SWIFTTransfer(Base):
    __tablename__ = "swift_transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    from_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    # Expéditeur
    sender_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_country: Mapped[str] = mapped_column(String(2), nullable=False)

    # Destinataire
    beneficiary_name: Mapped[str] = mapped_column(String(100), nullable=False)
    beneficiary_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    beneficiary_country: Mapped[str] = mapped_column(String(2), nullable=False)
    beneficiary_account: Mapped[str] = mapped_column(String(50), nullable=False)
    beneficiary_bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    beneficiary_bic: Mapped[str] = mapped_column(String(11), nullable=False)

    # Montants
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("1.0"))
    amount_in_eur: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total_deducted: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Message SWIFT
    message_type: Mapped[str] = mapped_column(String(10), default="MT103")
    purpose_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    remittance_info: Mapped[str | None] = mapped_column(String(140), nullable=True)

    # Statut
    status: Mapped[str] = mapped_column(String(20), default="pending")
    aml_status: Mapped[str] = mapped_column(String(20), default="cleared")
    aml_flags: Mapped[dict] = mapped_column(JSONB, default=dict)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_arrival: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_swift_user_id", "user_id"),
        Index("idx_swift_status", "status"),
        Index("idx_swift_reference", "reference"),
    )
