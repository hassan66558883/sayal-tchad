from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

INVOICE_STATES = ["draft", "validated", "cancelled"]
MOVE_TYPES = ["invoice", "credit_note"]
PAYMENT_STATES = ["not_paid", "partially_paid", "paid"]


class Invoice(Base, AuditedMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    move_type: Mapped[str] = mapped_column(String(16), default="invoice")
    sale_order_id: Mapped[int | None] = mapped_column(ForeignKey("sale_orders.id"))
    origin_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("partners.id"))
    invoice_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="draft")
    amount_total: Mapped[float] = mapped_column(Float, default=0.0)

    sale_order = relationship("SaleOrder")
    origin_invoice = relationship("Invoice", remote_side=[id])
    customer = relationship("Partner")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    __table_args__ = (
        CheckConstraint("qty > 0", name="invoice_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="invoice_line_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)

    invoice = relationship("Invoice", back_populates="lines")
    product = relationship("Product")

    @property
    def subtotal(self) -> float:
        return self.qty * self.unit_price


class Payment(Base, AuditedMixin):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="payment_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    amount: Mapped[float] = mapped_column(Float)
    payment_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="draft")

    invoice = relationship("Invoice", back_populates="payments")
