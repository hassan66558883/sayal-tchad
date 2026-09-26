from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin


class SalesRep(Base, AuditedMixin):
    """A commercial (sales rep), optionally linked to a user account so
    a "Mes ventes" restricted view is possible later - the same
    optional-user-link pattern already used for Driver (Phase 6).
    """

    __tablename__ = "sales_reps"
    __table_args__ = (
        CheckConstraint(
            "commission_rate >= 0 AND commission_rate <= 100", name="sales_rep_commission_rate_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(default=True)

    user = relationship("User", foreign_keys=[user_id])


class SalesTarget(Base, AuditedMixin):
    """A sales rep's objective for a period. Achievement is never
    stored - always computed live from that rep's real confirmed sale
    orders in the period (app/services/commercial.py), the same
    discipline used throughout this project for every derived figure.
    """

    __tablename__ = "sales_targets"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="sales_target_amount_positive"),
        CheckConstraint("period_end >= period_start", name="sales_target_period_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sales_rep_id: Mapped[int] = mapped_column(ForeignKey("sales_reps.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    target_amount: Mapped[float] = mapped_column(Float)

    sales_rep = relationship("SalesRep")
