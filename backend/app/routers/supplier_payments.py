from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.finance import SupplierInvoice, SupplierPayment
from app.models.user import User
from app.schemas.finance import SupplierPaymentCreate, SupplierPaymentRead
from app.services.finance import validate_payment_method_target
from app.services.sequence import next_reference
from app.services.supplier_invoice import get_other_confirmed_supplier_payments_total

SUPPLIER_PAYMENT_MANAGERS = ("caissier", "comptable", "direction_generale")

router = APIRouter(prefix="/api/supplier-payments", tags=["supplier-payments"])


@router.get("", response_model=list[SupplierPaymentRead])
def list_supplier_payments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(SupplierPayment).all()


@router.post("", response_model=SupplierPaymentRead, status_code=status.HTTP_201_CREATED)
def create_supplier_payment(
    payload: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SUPPLIER_PAYMENT_MANAGERS)),
):
    invoice = db.get(SupplierInvoice, payload.invoice_id)
    if invoice is None or invoice.state != "validated":
        raise HTTPException(status_code=400, detail="La facture fournisseur doit etre validee pour recevoir un paiement.")
    validate_payment_method_target(db, payload.payment_method, payload.cash_session_id, payload.bank_account_id)
    payment = SupplierPayment(
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_date=payload.payment_date,
        state="draft",
        payment_method=payload.payment_method,
        cash_session_id=payload.cash_session_id,
        bank_account_id=payload.bank_account_id,
    )
    payment.reference = next_reference(db, code="supplier_payment", prefix="PAF")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/confirm", response_model=SupplierPaymentRead)
def confirm_supplier_payment(
    payment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SUPPLIER_PAYMENT_MANAGERS))
):
    payment = db.get(SupplierPayment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if payment.state != "draft":
        raise HTTPException(status_code=400, detail="Seul un paiement en brouillon peut etre confirme.")

    invoice = payment.invoice
    other_confirmed = get_other_confirmed_supplier_payments_total(db, invoice.id, exclude_payment_id=payment.id)
    if other_confirmed + payment.amount > invoice.amount_total:
        raise HTTPException(status_code=400, detail="Ce paiement depasse le reste a payer de la facture.")
    payment.state = "confirmed"
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/cancel", response_model=SupplierPaymentRead)
def cancel_supplier_payment(
    payment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SUPPLIER_PAYMENT_MANAGERS))
):
    payment = db.get(SupplierPayment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if payment.state != "draft":
        raise HTTPException(status_code=400, detail="Un paiement confirme est immuable et ne peut pas etre annule.")
    payment.state = "cancelled"
    db.commit()
    db.refresh(payment)
    return payment
