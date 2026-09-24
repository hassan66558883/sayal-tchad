from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.import_ import Import
from app.models.purchase import PurchaseOrder, PurchaseOrderLine
from app.models.stock import StockMove


def get_qty_on_hand(db: Session, product_id: int, warehouse_id: int | None = None) -> float:
    """Sums done stock moves for a product: in/adjustment_in credit the
    destination warehouse, out/adjustment_out/transfer debit the source,
    transfer also credits its destination. Restricted to a single
    warehouse when warehouse_id is given, otherwise summed globally.
    """

    def _sum(move_types: list[str], warehouse_column) -> float:
        stmt = select(func.coalesce(func.sum(StockMove.qty), 0.0)).where(
            StockMove.product_id == product_id,
            StockMove.state == "done",
            StockMove.move_type.in_(move_types),
        )
        if warehouse_id is not None:
            stmt = stmt.where(warehouse_column == warehouse_id)
        return db.execute(stmt).scalar_one()

    credited = _sum(["in", "adjustment_in", "transfer"], StockMove.dest_warehouse_id)
    debited = _sum(["out", "adjustment_out", "transfer"], StockMove.source_warehouse_id)
    return credited - debited


def get_qty_in_transit(db: Session, product_id: int) -> float:
    """Ordered but not yet received: confirmed purchase order lines for
    this product whose import (if any) has not reached "receptionne".
    """

    stmt = (
        select(func.coalesce(func.sum(PurchaseOrderLine.qty), 0.0))
        .join(PurchaseOrder, PurchaseOrderLine.order_id == PurchaseOrder.id)
        .outerjoin(Import, Import.purchase_order_id == PurchaseOrder.id)
        .where(
            PurchaseOrderLine.product_id == product_id,
            PurchaseOrder.state == "commande",
            (Import.id.is_(None)) | (Import.state != "receptionne"),
        )
    )
    return db.execute(stmt).scalar_one()
