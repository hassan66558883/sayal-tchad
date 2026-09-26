from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.invoice import Invoice, InvoiceLine
from app.models.sale import SaleOrder
from app.models.user import User
from app.schemas.invoice import CreditNoteCreate, InvoiceCreateFromOrder, InvoiceRead
from app.services.invoice import get_payment_summary
from app.services.sequence import next_reference

SALES_MANAGERS = ("ventes", "direction_generale")

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _to_read(db: Session, invoice: Invoice) -> InvoiceRead:
    summary = get_payment_summary(db, invoice)
    return InvoiceRead(
        id=invoice.id,
        reference=invoice.reference,
        move_type=invoice.move_type,
        sale_order_id=invoice.sale_order_id,
        origin_invoice_id=invoice.origin_invoice_id,
        customer_id=invoice.customer_id,
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


@router.get("", response_model=list[InvoiceRead])
def list_invoices(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_to_read(db, inv) for inv in db.query(Invoice).all()]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def read_invoice(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    return _to_read(db, invoice)


@router.post("/from-order", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice_from_order(
    payload: InvoiceCreateFromOrder,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SALES_MANAGERS)),
):
    order = db.get(SaleOrder, payload.sale_order_id)
    if order is None or order.state != "commande":
        raise HTTPException(status_code=400, detail="La commande doit etre confirmee (etat 'commande') pour etre facturee.")

    invoice = Invoice(
        move_type="invoice",
        sale_order_id=order.id,
        customer_id=order.customer_id,
        invoice_date=order.order_date,
        state="draft",
        amount_total=order.amount_total,
    )
    invoice.reference = next_reference(db, code="invoice", prefix="FAC")
    for line in order.lines:
        invoice.lines.append(InvoiceLine(product_id=line.product_id, qty=line.qty, unit_price=line.unit_price))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return _to_read(db, invoice)


@router.post("/credit-notes", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_credit_note(
    payload: CreditNoteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SALES_MANAGERS)),
):
    origin = db.get(Invoice, payload.origin_invoice_id)
    if origin is None or origin.move_type != "invoice" or origin.state != "validated":
        raise HTTPException(status_code=400, detail="La facture d'origine doit etre une facture validee.")

    credit_note = Invoice(
        move_type="credit_note",
        origin_invoice_id=origin.id,
        customer_id=origin.customer_id,
        invoice_date=payload.invoice_date,
        state="draft",
    )
    credit_note.reference = next_reference(db, code="invoice", prefix="FAC")
    for line_payload in payload.lines:
        credit_note.lines.append(InvoiceLine(**line_payload.model_dump()))
    credit_note.amount_total = sum(line.subtotal for line in credit_note.lines)
    db.add(credit_note)
    db.commit()
    db.refresh(credit_note)
    return _to_read(db, credit_note)


@router.post("/{invoice_id}/validate", response_model=InvoiceRead)
def validate_invoice(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SALES_MANAGERS))):
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    if invoice.state != "draft":
        raise HTTPException(status_code=400, detail="Seule une facture en brouillon peut etre validee.")
    if not invoice.lines:
        raise HTTPException(status_code=400, detail="Impossible de valider une facture sans ligne.")
    invoice.state = "validated"
    db.commit()
    db.refresh(invoice)
    return _to_read(db, invoice)


@router.post("/{invoice_id}/cancel", response_model=InvoiceRead)
def cancel_invoice(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SALES_MANAGERS))):
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    summary = get_payment_summary(db, invoice)
    if summary.amount_paid > 0:
        raise HTTPException(status_code=400, detail="Impossible d'annuler une facture deja payee, meme partiellement.")
    if invoice.state == "cancelled":
        raise HTTPException(status_code=400, detail="Cette facture est deja annulee.")
    invoice.state = "cancelled"
    db.commit()
    db.refresh(invoice)
    return _to_read(db, invoice)
