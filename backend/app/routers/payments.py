from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.invoice import Invoice, Payment
from app.models.user import User
from app.schemas.invoice import PaymentCreate, PaymentRead
from app.services.invoice import get_other_confirmed_payments_total
from app.services.sequence import next_reference

PAYMENT_MANAGERS = ("caissier", "comptable", "direction_generale")

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead])
def list_payments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Payment).all()


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PAYMENT_MANAGERS)),
):
    invoice = db.get(Invoice, payload.invoice_id)
    if invoice is None or invoice.state != "validated":
        raise HTTPException(status_code=400, detail="La facture doit etre validee pour recevoir un paiement.")
    payment = Payment(
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_date=payload.payment_date,
        state="draft",
    )
    payment.reference = next_reference(db, code="payment", prefix="PAI")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/confirm", response_model=PaymentRead)
def confirm_payment(
    payment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*PAYMENT_MANAGERS))
):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if payment.state != "draft":
        raise HTTPException(status_code=400, detail="Seul un paiement en brouillon peut etre confirme.")

    invoice = payment.invoice
    other_confirmed = get_other_confirmed_payments_total(db, invoice.id, exclude_payment_id=payment.id)
    if other_confirmed + payment.amount > invoice.amount_total:
        raise HTTPException(
            status_code=400,
            detail="Ce paiement depasse le reste a payer de la facture.",
        )
    payment.state = "confirmed"
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/cancel", response_model=PaymentRead)
def cancel_payment(
    payment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*PAYMENT_MANAGERS))
):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if payment.state != "draft":
        raise HTTPException(status_code=400, detail="Un paiement confirme est immuable et ne peut pas etre annule.")
    payment.state = "cancelled"
    db.commit()
    db.refresh(payment)
    return payment
