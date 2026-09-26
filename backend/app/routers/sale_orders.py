from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.commercial import SalesRep
from app.models.partner import Partner
from app.models.product import Product
from app.models.sale import SaleOrder, SaleOrderLine
from app.models.user import User
from app.schemas.sale import SaleOrderCreate, SaleOrderLineCreate, SaleOrderRead
from app.services.customer_balance import get_customer_balance
from app.services.rbac import scope_by_branch
from app.services.sequence import next_reference

SALES_MANAGERS = ("ventes", "direction_generale")

router = APIRouter(prefix="/api/sale-orders", tags=["sale-orders"])


def _recompute_total(order: SaleOrder) -> None:
    order.amount_total = sum(line.subtotal for line in order.lines)


@router.get("", response_model=list[SaleOrderRead])
def list_sale_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(SaleOrder)
    stmt = scope_by_branch(stmt, SaleOrder.branch_id, current_user)
    return db.execute(stmt).scalars().unique().all()


@router.get("/{order_id}", response_model=SaleOrderRead)
def read_sale_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.get(SaleOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    return order


@router.post("", response_model=SaleOrderRead, status_code=status.HTTP_201_CREATED)
def create_sale_order(
    payload: SaleOrderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SALES_MANAGERS)),
):
    customer = db.get(Partner, payload.customer_id)
    if customer is None or not customer.is_customer:
        raise HTTPException(status_code=400, detail="Client invalide.")
    if payload.sales_rep_id is not None and db.get(SalesRep, payload.sales_rep_id) is None:
        raise HTTPException(status_code=400, detail="Commercial introuvable.")

    order = SaleOrder(
        customer_id=payload.customer_id,
        branch_id=payload.branch_id,
        sales_rep_id=payload.sales_rep_id,
        order_date=payload.order_date,
        state="devis",
    )
    order.reference = next_reference(db, code="sale_order", prefix="CMD")
    for line_payload in payload.lines:
        if db.get(Product, line_payload.product_id) is None:
            raise HTTPException(status_code=400, detail="Produit introuvable dans une ligne.")
        order.lines.append(SaleOrderLine(**line_payload.model_dump()))
    _recompute_total(order)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/lines", response_model=SaleOrderRead)
def add_line(
    order_id: int,
    payload: SaleOrderLineCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SALES_MANAGERS)),
):
    order = db.get(SaleOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    if order.state != "devis":
        raise HTTPException(status_code=400, detail="Impossible d'ajouter une ligne hors de l'etat devis.")
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=400, detail="Produit introuvable.")
    order.lines.append(SaleOrderLine(**payload.model_dump()))
    _recompute_total(order)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/confirm", response_model=SaleOrderRead)
def confirm_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SALES_MANAGERS))):
    order = db.get(SaleOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    if order.state != "devis":
        raise HTTPException(status_code=400, detail="Seul un devis peut etre confirme.")
    if not order.lines:
        raise HTTPException(status_code=400, detail="Impossible de confirmer une commande sans ligne.")

    customer = order.customer
    if customer.credit_limit > 0:
        current_balance = get_customer_balance(db, customer.id)
        if current_balance + order.amount_total > customer.credit_limit:
            raise HTTPException(
                status_code=400,
                detail="Limite de credit du client depassee : confirmation refusee.",
            )

    order.state = "commande"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/terminate", response_model=SaleOrderRead)
def terminate_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SALES_MANAGERS))):
    order = db.get(SaleOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    if order.state != "commande":
        raise HTTPException(status_code=400, detail="Seule une commande confirmee peut etre terminee.")
    order.state = "terminee"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=SaleOrderRead)
def cancel_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*SALES_MANAGERS))):
    order = db.get(SaleOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    if order.state not in ("devis", "commande"):
        raise HTTPException(status_code=400, detail="Cette commande ne peut plus etre annulee.")
    order.state = "annulee"
    db.commit()
    db.refresh(order)
    return order
