import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Table, Column
from app.core.database import Base

users_table = Table("users", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), extend_existing=True)
accounts_table = Table("accounts", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), Column("user_id", UUID(as_uuid=True)), extend_existing=True)

class SEPATransfer(Base):
    __tablename__ = "sepa_transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    end_to_end_id: Mapped[str] = mapped_column(String(35), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    from_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    # Expéditeur
    debtor_name: Mapped[str] = mapped_column(String(70), nullable=False)
    debtor_iban: Mapped[str] = mapped_column(String(34), nullable=False)
    debtor_bic: Mapped[str] = mapped_column(String(11), nullable=False)

    # Destinataire
    creditor_name: Mapped[str] = mapped_column(String(70), nullable=False)
    creditor_iban: Mapped[str] = mapped_column(String(34), nullable=False)
    creditor_bic: Mapped[str | None] = mapped_column(String(11), nullable=True)
    creditor_country: Mapped[str] = mapped_column(String(2), nullable=False)

    # Montant
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.50"))

    # Type SEPA
    transfer_type: Mapped[str] = mapped_column(String(20), default="SCT")
    is_instant: Mapped[bool] = mapped_column(Boolean, default=False)

    # Informations
    remittance_info: Mapped[str | None] = mapped_column(String(140), nullable=True)
    purpose_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Statut
    status: Mapped[str] = mapped_column(String(20), default="pending")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settlement_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_sepa_user_id", "user_id"),
        Index("idx_sepa_status", "status"),
        Index("idx_sepa_reference", "reference"),
    )
