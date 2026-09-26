from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.finance import SupplierInvoice, SupplierInvoiceLine
from app.models.purchase import PurchaseOrder
from app.models.user import User
from app.schemas.finance import SupplierDebitNoteCreate, SupplierInvoiceCreateFromOrder, SupplierInvoiceRead
from app.services.sequence import next_reference
from app.services.supplier_invoice import get_supplier_payment_summary

SUPPLIER_INVOICE_MANAGERS = ("comptable", "achats", "direction_generale")

router = APIRouter(prefix="/api/supplier-invoices", tags=["supplier-invoices"])


def _to_read(db: Session, invoice: SupplierInvoice) -> SupplierInvoiceRead:
    summary = get_supplier_payment_summary(db, invoice)
    return SupplierInvoiceRead(
        id=invoice.id,
        reference=invoice.reference,
        move_type=invoice.move_type,
        purchase_order_id=invoice.purchase_order_id,
        origin_invoice_id=invoice.origin_invoice_id,
        supplier_id=invoice.supplier_id,
        invoice_date=invoice.invoice_date,
        state=invoice.state,
        amount_total=invoice.amount_total,
        amount_paid=summary.amount_paid,
        amount_due=summary.amount_due,
        payment_state=summary.payment_state,
        lines=[
            {
                "id": line.id,
                "product_id": line.product_id,
                "qty": line.qty,
                "unit_price": line.unit_price,
                "subtotal": line.subtotal,
            }
            for line in invoice.lines
        ],
    )


@router.get("", response_model=list[SupplierInvoiceRead])
def list_supplier_invoices(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_to_read(db, inv) for inv in db.query(SupplierInvoice).all()]


@router.get("/{invoice_id}", response_model=SupplierInvoiceRead)
def read_supplier_invoice(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    invoice = db.get(SupplierInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture fournisseur introuvable.")
    return _to_read(db, invoice)


@router.post("/from-order", response_model=SupplierInvoiceRead, status_code=status.HTTP_201_CREATED)
def create_supplier_invoice_from_order(
    payload: SupplierInvoiceCreateFromOrder,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SUPPLIER_INVOICE_MANAGERS)),
):
    order = db.get(PurchaseOrder, payload.purchase_order_id)
    if order is None or order.state != "commande":
        raise HTTPException(
            status_code=400, detail="La commande d'achat doit etre confirmee (etat 'commande') pour etre facturee."
        )
    if db.query(SupplierInvoice).filter(SupplierInvoice.purchase_order_id == order.id).count():
        raise HTTPException(status_code=400, detail="Cette commande d'achat a deja une facture fournisseur.")

    invoice = SupplierInvoice(
        move_type="bill",
        purchase_order_id=order.id,
        supplier_id=order.supplier_id,
        invoice_date=order.order_date,
        state="draft",
        amount_total=order.amount_total,
    )
    invoice.reference = next_reference(db, code="supplier_invoice", prefix="FRS")
    for line in order.lines:
        invoice.lines.append(SupplierInvoiceLine(product_id=line.product_id, qty=line.qty, unit_price=line.unit_price))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return _to_read(db, invoice)


@router.post("/debit-notes", response_model=SupplierInvoiceRead, status_code=status.HTTP_201_CREATED)
def create_debit_note(
    payload: SupplierDebitNoteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SUPPLIER_INVOICE_MANAGERS)),
):
    origin = db.get(SupplierInvoice, payload.origin_invoice_id)
    if origin is None or origin.move_type != "bill" or origin.state != "validated":
        raise HTTPException(status_code=400, detail="La facture d'origine doit etre une facture fournisseur validee.")

    debit_note = SupplierInvoice(
        move_type="debit_note",
        origin_invoice_id=origin.id,
        supplier_id=origin.supplier_id,
        invoice_date=payload.invoice_date,
        state="draft",
    )
    debit_note.reference = next_reference(db, code="supplier_invoice", prefix="FRS")
    for line_payload in payload.lines:
        debit_note.lines.append(SupplierInvoiceLine(**line_payload.model_dump()))
    debit_note.amount_total = sum(line.subtotal for line in debit_note.lines)
    db.add(debit_note)
    db.commit()
    db.refresh(debit_note)
    return _to_read(db, debit_note)


@router.post("/{invoice_id}/validate", response_model=SupplierInvoiceRead)
def validate_supplier_invoice(
    invoice_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SUPPLIER_INVOICE_MANAGERS))
):
    invoice = db.get(SupplierInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture fournisseur introuvable.")
    if invoice.state != "draft":
        raise HTTPException(status_code=400, detail="Seule une facture en brouillon peut etre validee.")
    if not invoice.lines:
        raise HTTPException(status_code=400, detail="Impossible de valider une facture sans ligne.")
    invoice.state = "validated"
    db.commit()
    db.refresh(invoice)
    return _to_read(db, invoice)


@router.post("/{invoice_id}/cancel", response_model=SupplierInvoiceRead)
def cancel_supplier_invoice(
    invoice_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SUPPLIER_INVOICE_MANAGERS))
):
    invoice = db.get(SupplierInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture fournisseur introuvable.")
    summary = get_supplier_payment_summary(db, invoice)
    if summary.amount_paid > 0:
        raise HTTPException(status_code=400, detail="Impossible d'annuler une facture deja payee, meme partiellement.")
    if invoice.state == "cancelled":
        raise HTTPException(status_code=400, detail="Cette facture est deja annulee.")
    invoice.state = "cancelled"
    db.commit()
    db.refresh(invoice)
    return _to_read(db, invoice)
