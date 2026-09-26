"""Invoice payment figures, computed live from real Payment rows rather
than stored/cached - deliberately avoiding the exact "computed field
goes stale without @api.depends" bug class that had to be fixed
retroactively in the prior Odoo-based build of this project, and the
"compares a payment against its own already-updated amount_due" self-
counting bug that was caught and fixed there too (side-stepped here
entirely: overpayment is checked against a live SUM of OTHER confirmed
payments, never a cached total).
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, Payment


@dataclass
class InvoicePaymentSummary:
    amount_paid: float
    amount_due: float
    payment_state: str


def get_payment_summary(db: Session, invoice: Invoice) -> InvoicePaymentSummary:
    paid = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.invoice_id == invoice.id, Payment.state == "confirmed"
        )
    ).scalar_one()
    due = invoice.amount_total - paid
    if invoice.amount_total <= 0 or paid <= 0:
        state = "not_paid"
    elif paid >= invoice.amount_total:
        state = "paid"
    else:
        state = "partially_paid"
    return InvoicePaymentSummary(amount_paid=paid, amount_due=due, payment_state=state)


def get_other_confirmed_payments_total(db: Session, invoice_id: int, exclude_payment_id: int | None) -> float:
    stmt = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
        Payment.invoice_id == invoice_id, Payment.state == "confirmed"
    )
    if exclude_payment_id is not None:
        stmt = stmt.where(Payment.id != exclude_payment_id)
    return db.execute(stmt).scalar_one()
