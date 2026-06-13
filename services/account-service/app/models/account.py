import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from sqlalchemy import Table, Column

# Référence légère à la table "users" (gérée par auth-service) pour résoudre la FK
users_table = Table(
    "users", Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    extend_existing=True,
)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    iban: Mapped[str | None] = mapped_column(String(34), unique=True, nullable=True)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_transfer_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("10000.00"))
    monthly_transfer_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("50000.00"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_accounts_user_id", "user_id"),
        Index("idx_accounts_status", "status"),
    )
