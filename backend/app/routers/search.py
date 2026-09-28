"""Global search across the main business entities. A thin ILIKE lookup
over a handful of tables, capped per category - no ranking engine, just
enough to jump straight to a record by name or reference.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.delivery import Delivery
from app.models.invoice import Invoice
from app.models.partner import Partner
from app.models.product import Product
from app.models.sale import SaleOrder
from app.models.user import User

router = APIRouter(prefix="/api/search", tags=["search"])

LIMIT_PER_CATEGORY = 6


@router.get("")
def search(
    q: str = Query(min_length=2),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    like = f"%{q}%"

    partners = (
        db.query(Partner)
        .filter(or_(Partner.name.ilike(like), Partner.reference.ilike(like)))
        .limit(LIMIT_PER_CATEGORY)
        .all()
    )
    products = (
        db.query(Product)
        .filter(or_(Product.name.ilike(like), Product.reference.ilike(like)))
        .limit(LIMIT_PER_CATEGORY)
        .all()
    )
    invoices = db.query(Invoice).filter(Invoice.reference.ilike(like)).limit(LIMIT_PER_CATEGORY).all()
    sale_orders = db.query(SaleOrder).filter(SaleOrder.reference.ilike(like)).limit(LIMIT_PER_CATEGORY).all()
    deliveries = db.query(Delivery).filter(Delivery.reference.ilike(like)).limit(LIMIT_PER_CATEGORY).all()

    return {
        "partners": [
            {"id": p.id, "label": p.name, "sublabel": p.reference, "path": "/partners"} for p in partners
        ],
        "products": [
            {"id": p.id, "label": p.name, "sublabel": p.reference, "path": "/products"} for p in products
        ],
        "invoices": [
            {"id": i.id, "label": i.reference, "sublabel": f"{i.amount_total:g} FCFA", "path": "/invoices"}
            for i in invoices
        ],
        "sale_orders": [
            {"id": o.id, "label": o.reference, "sublabel": o.state, "path": "/sale-orders"} for o in sale_orders
        ],
        "deliveries": [
            {"id": d.id, "label": d.reference, "sublabel": d.state, "path": "/deliveries"} for d in deliveries
        ],
    }
