from datetime import date, datetime, time

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


def get_warehouse_summary(db: Session, warehouse_id: int, period_start: date, period_end: date) -> dict:
    """Current total stock (all products, all-time, done moves) plus
    incoming/outgoing movement totals for the given period - the same
    credit/debit logic as get_qty_on_hand, just without a product filter.
    """

    def _sum(
        move_types: list[str], warehouse_column, since: datetime | None = None, until: datetime | None = None
    ) -> float:
        stmt = select(func.coalesce(func.sum(StockMove.qty), 0.0)).where(
            warehouse_column == warehouse_id,
            StockMove.state == "done",
            StockMove.move_type.in_(move_types),
        )
        if since is not None:
            stmt = stmt.where(StockMove.move_date >= since)
        if until is not None:
            stmt = stmt.where(StockMove.move_date <= until)
        return db.execute(stmt).scalar_one()

    period_start_dt = datetime.combine(period_start, time.min)
    period_end_dt = datetime.combine(period_end, time.max)

    current_in = _sum(["in", "adjustment_in", "transfer"], StockMove.dest_warehouse_id)
    current_out = _sum(["out", "adjustment_out", "transfer"], StockMove.source_warehouse_id)
    incoming = _sum(["in", "adjustment_in", "transfer"], StockMove.dest_warehouse_id, period_start_dt, period_end_dt)
    outgoing = _sum(["out", "adjustment_out", "transfer"], StockMove.source_warehouse_id, period_start_dt, period_end_dt)
    transfers_in = _sum(["transfer"], StockMove.dest_warehouse_id, period_start_dt, period_end_dt)

    return {
        "warehouse_id": warehouse_id,
        "current_qty": current_in - current_out,
        "incoming_qty": incoming,
        "outgoing_qty": outgoing,
        "transfers_qty": transfers_in,
    }


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
