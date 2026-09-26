"""Payable-side mirror of app.services.invoice: amount_paid/amount_due/
payment_state always computed live from real SupplierPayment rows, and
overpayment is checked against a live SUM of the invoice's OTHER
confirmed payments - the same two anti-patterns (stale cached fields,
self-counting overpayment checks) deliberately avoided throughout this
project are avoided here too.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finance import SupplierInvoice, SupplierPayment


@dataclass
class SupplierInvoicePaymentSummary:
    amount_paid: float
    amount_due: float
    payment_state: str


def get_supplier_payment_summary(db: Session, invoice: SupplierInvoice) -> SupplierInvoicePaymentSummary:
    paid = db.execute(
        select(func.coalesce(func.sum(SupplierPayment.amount), 0.0)).where(
            SupplierPayment.invoice_id == invoice.id, SupplierPayment.state == "confirmed"
        )
    ).scalar_one()
    due = invoice.amount_total - paid
    if invoice.amount_total <= 0 or paid <= 0:
        state = "not_paid"
    elif paid >= invoice.amount_total:
        state = "paid"
    else:
        state = "partially_paid"
    return SupplierInvoicePaymentSummary(amount_paid=paid, amount_due=due, payment_state=state)


def get_other_confirmed_supplier_payments_total(db: Session, invoice_id: int, exclude_payment_id: int | None) -> float:
    stmt = select(func.coalesce(func.sum(SupplierPayment.amount), 0.0)).where(
        SupplierPayment.invoice_id == invoice_id, SupplierPayment.state == "confirmed"
    )
    if exclude_payment_id is not None:
        stmt = stmt.where(SupplierPayment.id != exclude_payment_id)
    return db.execute(stmt).scalar_one()


def get_supplier_balance(db: Session, supplier_id: int) -> float:
    """Sum of validated bills' amount_due minus validated debit notes'
    amount_due (mirrors app.services.customer_balance.get_customer_balance).
    """

    invoices = (
        db.query(SupplierInvoice)
        .filter(SupplierInvoice.supplier_id == supplier_id, SupplierInvoice.state == "validated")
        .all()
    )
    total = 0.0
    for invoice in invoices:
        sign = 1 if invoice.move_type == "bill" else -1
        summary = get_supplier_payment_summary(db, invoice)
        total += sign * summary.amount_due
    return total
