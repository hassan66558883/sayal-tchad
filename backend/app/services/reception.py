from sqlalchemy.orm import Session

from app.models.import_ import Import
from app.models.stock import StockMove


def create_reception_moves(db: Session, import_record: Import, warehouse_id: int) -> list[StockMove]:
    """Bridges a receptionne import to real (draft) stock entries, one
    per purchase order line - the same role seyal.stock.reception.wizard
    played in the original design.
    """

    moves = []
    for line in import_record.purchase_order.lines:
        move = StockMove(
            move_type="in",
            product_id=line.product_id,
            qty=line.qty,
            dest_warehouse_id=warehouse_id,
            state="draft",
            reason=f"Reception {import_record.reference}",
        )
        db.add(move)
        moves.append(move)
    db.flush()
    return moves
