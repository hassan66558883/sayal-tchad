from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

PAYMENT_METHODS = ["especes", "banque"]

SUPPLIER_INVOICE_STATES = ["draft", "validated", "cancelled"]
SUPPLIER_MOVE_TYPES = ["bill", "debit_note"]

CASH_SESSION_STATES = ["open", "closed"]
EXPENSE_STATES = ["draft", "validated", "cancelled"]
BANK_TRANSACTION_TYPES = ["in", "out"]


class SupplierInvoice(Base, AuditedMixin):
    """The payable-side mirror of Invoice (app.models.invoice): a vendor
    bill against a received purchase order, or a debit note against a
    validated bill (the supplier-side equivalent of a credit note).
    """

    __tablename__ = "supplier_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    move_type: Mapped[str] = mapped_column(String(16), default="bill")
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    origin_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_invoices.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), index=True)
    invoice_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="draft")
    amount_total: Mapped[float] = mapped_column(Float, default=0.0)

    purchase_order = relationship("PurchaseOrder")
    origin_invoice = relationship("SupplierInvoice", remote_side=[id])
    supplier = relationship("Partner")
    lines = relationship("SupplierInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("SupplierPayment", back_populates="invoice")


class SupplierInvoiceLine(Base):
    __tablename__ = "supplier_invoice_lines"
    __table_args__ = (
        CheckConstraint("qty > 0", name="supplier_invoice_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="supplier_invoice_line_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("supplier_invoices.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)

    invoice = relationship("SupplierInvoice", back_populates="lines")
    product = relationship("Product")

    @property
    def subtotal(self) -> float:
        return self.qty * self.unit_price


class CashRegister(Base, AuditedMixin):
    __tablename__ = "cash_registers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32), unique=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    branch = relationship("Branch")


class CashSession(Base, AuditedMixin):
    """Open -> closed. Its real cash balance (opening_balance plus every
    confirmed cash payment/expense tagged with this session) is always
    computed live from those rows (app.services.finance) rather than
    stored, so it can never drift out of sync - closing merely records
    the physically counted amount for a variance check against it,
    mirroring the theoretical-vs-counted pattern already used for
    stock inventories (Phase 4).
    """

    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    register_id: Mapped[int] = mapped_column(ForeignKey("cash_registers.id"), index=True)
    state: Mapped[str] = mapped_column(String(16), default="open")
    opening_balance: Mapped[float] = mapped_column(Float, default=0.0)
    closing_balance: Mapped[float | None] = mapped_column(Float)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    register = relationship("CashRegister")


class BankAccount(Base, AuditedMixin):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    bank_name: Mapped[str] = mapped_column(String(255))
    account_number: Mapped[str] = mapped_column(String(64), unique=True)
    opening_balance: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BankTransaction(Base, AuditedMixin):
    """Manual bank ledger entries (capital injection, bank fees, a
    transfer not tied to any invoice/expense) - final once created, the
    same "complete, tamper-evident history" requirement as stock moves.
    """

    __tablename__ = "bank_transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="bank_transaction_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_account_id: Mapped[int] = mapped_column(ForeignKey("bank_accounts.id"))
    movement_type: Mapped[str] = mapped_column(String(8))
    amount: Mapped[float] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(String(255))
    transaction_date: Mapped[date] = mapped_column(Date)

    bank_account = relationship("BankAccount")


class Expense(Base, AuditedMixin):
    __tablename__ = "expenses"
    __table_args__ = (CheckConstraint("amount > 0", name="expense_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    category: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    expense_date: Mapped[date] = mapped_column(Date)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    state: Mapped[str] = mapped_column(String(16), default="draft")
    payment_method: Mapped[str] = mapped_column(String(16), default="especes")
    cash_session_id: Mapped[int | None] = mapped_column(ForeignKey("cash_sessions.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank_accounts.id"))

    branch = relationship("Branch")
    cash_session = relationship("CashSession")
    bank_account = relationship("BankAccount")


class SupplierPayment(Base, AuditedMixin):
    __tablename__ = "supplier_payments"
    __table_args__ = (CheckConstraint("amount > 0", name="supplier_payment_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("supplier_invoices.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    payment_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="draft")
    payment_method: Mapped[str] = mapped_column(String(16), default="especes")
    cash_session_id: Mapped[int | None] = mapped_column(ForeignKey("cash_sessions.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank_accounts.id"))

    invoice = relationship("SupplierInvoice", back_populates="payments")
    cash_session = relationship("CashSession")
    bank_account = relationship("BankAccount")
