import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Table, Column
from app.core.database import Base

users_table = Table("users", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), extend_existing=True)
accounts_table = Table("accounts", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), Column("user_id", UUID(as_uuid=True)), extend_existing=True)

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    loan_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_requested: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)

    monthly_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    employment_status: Mapped[str] = mapped_column(String(50), nullable=False)
    credit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    monthly_payment: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_repayment: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_assessment: Mapped[dict] = mapped_column(JSONB, default=dict)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disbursed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_loan_user_id", "user_id"),
        Index("idx_loan_status", "status"),
    )


class LoanRepayment(Base):
    __tablename__ = "loan_repayments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    principal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    interest: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
