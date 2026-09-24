from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

CUSTOMER_TYPES = ["grossiste", "detaillant", "supermarche", "boutique", "institution"]


class Partner(Base, AuditedMixin):
    """Unified customer/supplier, matching the original design: one
    record can be a customer, a supplier, or both, distinguished by the
    is_customer/is_supplier flags rather than separate tables.
    """

    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    is_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_supplier: Mapped[bool] = mapped_column(Boolean, default=False)
    customer_type: Mapped[str | None] = mapped_column(String(32))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(255))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    salesperson_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    credit_limit: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    branch = relationship("Branch")
    salesperson = relationship("User", foreign_keys=[salesperson_id])
