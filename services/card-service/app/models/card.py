import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Boolean, Numeric, Integer, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Table, Column
from app.core.database import Base
from app.utils.encryption import encrypt_field, decrypt_field

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

class VirtualCard(Base):
    __tablename__ = "virtual_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    card_number_encrypted: Mapped[str] = mapped_column("card_number", String(255), unique=True, nullable=False)
    card_number_masked: Mapped[str] = mapped_column(String(19), nullable=False)

    @property
    def card_number(self) -> str:
        return decrypt_field(self.card_number_encrypted)

    @card_number.setter
    def card_number(self, value: str) -> None:
        self.card_number_encrypted = encrypt_field(value)
    card_holder_name: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_month: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cvv_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    card_type: Mapped[str] = mapped_column(String(20), default="visa")
    status: Mapped[str] = mapped_column(String(20), default="active")
    daily_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("1000.00"))
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("5000.00"))
    daily_spent: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    monthly_spent: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=True)
    is_contactless: Mapped[bool] = mapped_column(Boolean, default=True)
    is_online_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_international_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_cards_user_id", "user_id"),
        Index("idx_cards_account_id", "account_id"),
        Index("idx_cards_status", "status"),
    )
