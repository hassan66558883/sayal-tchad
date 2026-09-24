"""Real landed-cost allocation, mirroring the original design's "COUT
REEL" formula: purchase amount + transport/customs/transit/other costs,
spread pro rata across the purchase order's lines by each line's share
of the order subtotal, then written onto Product.cost_price.
"""

from sqlalchemy.orm import Session

from app.models.import_ import Import
from app.models.purchase import PurchaseOrder


def apply_real_cost_to_products(db: Session, import_record: Import) -> None:
    order: PurchaseOrder = import_record.purchase_order
    order_subtotal = sum(line.subtotal for line in order.lines)
    extra_costs = import_record.extra_costs_total

    for line in order.lines:
        share = (line.subtotal / order_subtotal) if order_subtotal > 0 else 0.0
        allocated_extra = share * extra_costs
        real_unit_cost = (line.subtotal + allocated_extra) / line.qty
        line.product.cost_price = real_unit_cost
    db.flush()
