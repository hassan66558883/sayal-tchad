from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.services.invoice import get_payment_summary


def get_customer_balance(db: Session, customer_id: int) -> float:
    """Sum of validated invoices' amount_due minus validated credit
    notes' amount_due (a credit note directly reduces what the customer
    owes, matching real-world behaviour).
    """

    invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id, Invoice.state == "validated").all()
    total = 0.0
    for invoice in invoices:
        sign = 1 if invoice.move_type == "invoice" else -1
        summary = get_payment_summary(db, invoice)
        total += sign * summary.amount_due
    return total
