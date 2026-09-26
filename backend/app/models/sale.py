from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

SALE_ORDER_STATES = ["devis", "commande", "terminee", "annulee"]


class SaleOrder(Base, AuditedMixin):
    __tablename__ = "sale_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("partners.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    order_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="devis")
    amount_total: Mapped[float] = mapped_column(Float, default=0.0)

    customer = relationship("Partner")
    branch = relationship("Branch")
    lines = relationship("SaleOrderLine", back_populates="order", cascade="all, delete-orphan")


class SaleOrderLine(Base):
    __tablename__ = "sale_order_lines"
    __table_args__ = (
        CheckConstraint("qty > 0", name="sale_order_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="sale_order_line_unit_price_non_negative"),
        CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100", name="sale_order_line_discount_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sale_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0)

    order = relationship("SaleOrder", back_populates="lines")
    product = relationship("Product")

    @property
    def subtotal(self) -> float:
        return self.qty * self.unit_price * (1 - self.discount_percent / 100)
