from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

PURCHASE_ORDER_STATES = ["proforma", "commande", "terminee", "annulee"]


class PurchaseOrder(Base, AuditedMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("partners.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    order_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="proforma")
    amount_total: Mapped[float] = mapped_column(Float, default=0.0)

    supplier = relationship("Partner")
    branch = relationship("Branch")
    lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")
    import_ = relationship("Import", back_populates="purchase_order", uselist=False)


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        CheckConstraint("qty > 0", name="purchase_order_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="purchase_order_line_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)

    order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")

    @property
    def subtotal(self) -> float:
        return self.qty * self.unit_price
