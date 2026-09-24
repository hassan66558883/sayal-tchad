from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.partner import Partner
from app.models.product import Product
from app.models.purchase import PurchaseOrder, PurchaseOrderLine
from app.models.user import User
from app.schemas.purchase import PurchaseOrderCreate, PurchaseOrderLineCreate, PurchaseOrderRead
from app.services.rbac import scope_by_branch
from app.services.sequence import next_reference

PURCHASE_MANAGERS = ("achats", "direction_generale")

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


def _recompute_total(order: PurchaseOrder) -> None:
    order.amount_total = sum(line.subtotal for line in order.lines)


@router.get("", response_model=list[PurchaseOrderRead])
def list_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(PurchaseOrder)
    stmt = scope_by_branch(stmt, PurchaseOrder.branch_id, current_user)
    return db.execute(stmt).scalars().unique().all()


@router.get("/{order_id}", response_model=PurchaseOrderRead)
def read_purchase_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande d'achat introuvable.")
    return order


@router.post("", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PURCHASE_MANAGERS)),
):
    supplier = db.get(Partner, payload.supplier_id)
    if supplier is None or not supplier.is_supplier:
        raise HTTPException(status_code=400, detail="Fournisseur invalide.")

    order = PurchaseOrder(
        supplier_id=payload.supplier_id,
        branch_id=payload.branch_id,
        order_date=payload.order_date,
        state="proforma",
    )
    order.reference = next_reference(db, code="purchase_order", prefix="ACH")
    for line_payload in payload.lines:
        if db.get(Product, line_payload.product_id) is None:
            raise HTTPException(status_code=400, detail="Produit introuvable dans une ligne.")
        order.lines.append(PurchaseOrderLine(**line_payload.model_dump()))
    _recompute_total(order)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/lines", response_model=PurchaseOrderRead)
def add_line(
    order_id: int,
    payload: PurchaseOrderLineCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PURCHASE_MANAGERS)),
):
    order = db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande d'achat introuvable.")
    if order.state != "proforma":
        raise HTTPException(status_code=400, detail="Impossible d'ajouter une ligne hors de l'etat proforma.")
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=400, detail="Produit introuvable.")
    order.lines.append(PurchaseOrderLine(**payload.model_dump()))
    _recompute_total(order)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/confirm", response_model=PurchaseOrderRead)
def confirm_order(
    order_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*PURCHASE_MANAGERS))
):
    order = db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande d'achat introuvable.")
    if order.state != "proforma":
        raise HTTPException(status_code=400, detail="Seule une commande proforma peut etre confirmee.")
    if not order.lines:
        raise HTTPException(status_code=400, detail="Impossible de confirmer une commande sans ligne.")
    order.state = "commande"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/terminate", response_model=PurchaseOrderRead)
def terminate_order(
    order_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*PURCHASE_MANAGERS))
):
    order = db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande d'achat introuvable.")
    if order.state != "commande":
        raise HTTPException(status_code=400, detail="Seule une commande confirmee peut etre terminee.")
    order.state = "terminee"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=PurchaseOrderRead)
def cancel_order(
    order_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*PURCHASE_MANAGERS))
):
    order = db.get(PurchaseOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande d'achat introuvable.")
    if order.state not in ("proforma", "commande"):
        raise HTTPException(status_code=400, detail="Cette commande ne peut plus etre annulee.")
    order.state = "annulee"
    db.commit()
    db.refresh(order)
    return order
