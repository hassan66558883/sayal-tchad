from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.product import Product
from app.models.stock import MOVE_TYPES, MOVE_TYPES_REQUIRING_DEST, MOVE_TYPES_REQUIRING_SOURCE, StockMove, Warehouse
from app.models.user import User
from app.schemas.stock import ProductStockRead, StockMoveCreate, StockMoveRead, StockMoveUpdate
from app.services.stock import get_qty_in_transit, get_qty_on_hand

STOCK_MANAGERS = ("stock", "direction_generale")

router = APIRouter(prefix="/api", tags=["stock"])


def _validate_warehouses(payload: StockMoveCreate) -> None:
    if payload.move_type not in MOVE_TYPES:
        raise HTTPException(status_code=400, detail="Type de mouvement invalide.")
    if payload.move_type in MOVE_TYPES_REQUIRING_SOURCE and payload.source_warehouse_id is None:
        raise HTTPException(status_code=400, detail="Un entrepot source est requis pour ce type de mouvement.")
    if payload.move_type in MOVE_TYPES_REQUIRING_DEST and payload.dest_warehouse_id is None:
        raise HTTPException(status_code=400, detail="Un entrepot de destination est requis pour ce type de mouvement.")


@router.get("/stock-moves", response_model=list[StockMoveRead])
def list_stock_moves(
    product_id: int | None = Query(default=None),
    warehouse_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(StockMove)
    if product_id is not None:
        query = query.filter(StockMove.product_id == product_id)
    if warehouse_id is not None:
        query = query.filter(
            (StockMove.source_warehouse_id == warehouse_id) | (StockMove.dest_warehouse_id == warehouse_id)
        )
    return query.order_by(StockMove.id.desc()).all()


@router.post("/stock-moves", response_model=StockMoveRead, status_code=status.HTTP_201_CREATED)
def create_stock_move(
    payload: StockMoveCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STOCK_MANAGERS)),
):
    _validate_warehouses(payload)
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=400, detail="Produit introuvable.")
    for warehouse_id in (payload.source_warehouse_id, payload.dest_warehouse_id):
        if warehouse_id is not None and db.get(Warehouse, warehouse_id) is None:
            raise HTTPException(status_code=400, detail="Entrepot introuvable.")
    move = StockMove(**payload.model_dump(), state="draft")
    db.add(move)
    db.commit()
    db.refresh(move)
    return move


@router.post("/stock-moves/{move_id}/validate", response_model=StockMoveRead)
def validate_stock_move(
    move_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*STOCK_MANAGERS))
):
    move = db.get(StockMove, move_id)
    if move is None:
        raise HTTPException(status_code=404, detail="Mouvement introuvable.")
    if move.state != "draft":
        raise HTTPException(status_code=400, detail="Seul un mouvement en brouillon peut etre valide.")
    move.state = "done"
    db.commit()
    db.refresh(move)
    return move


@router.patch("/stock-moves/{move_id}", response_model=StockMoveRead)
def update_stock_move(
    move_id: int,
    payload: StockMoveUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STOCK_MANAGERS)),
):
    move = db.get(StockMove, move_id)
    if move is None:
        raise HTTPException(status_code=404, detail="Mouvement introuvable.")
    changes = payload.model_dump(exclude_unset=True)
    if move.state == "done":
        disallowed = set(changes) - {"reason"}
        if disallowed:
            raise HTTPException(
                status_code=400,
                detail="Un mouvement valide est immuable : seul le motif (reason) peut etre modifie.",
            )
    else:
        merged = StockMoveCreate(
            move_type=changes.get("move_type", move.move_type),
            product_id=changes.get("product_id", move.product_id),
            qty=changes.get("qty", move.qty),
            source_warehouse_id=changes.get("source_warehouse_id", move.source_warehouse_id),
            dest_warehouse_id=changes.get("dest_warehouse_id", move.dest_warehouse_id),
            lot_id=changes.get("lot_id", move.lot_id),
            reason=changes.get("reason", move.reason),
        )
        _validate_warehouses(merged)
    for field, value in changes.items():
        setattr(move, field, value)
    db.commit()
    db.refresh(move)
    return move


@router.get("/products/{product_id}/stock", response_model=ProductStockRead)
def read_product_stock(
    product_id: int,
    warehouse_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return ProductStockRead(
        product_id=product_id,
        qty_on_hand=get_qty_on_hand(db, product_id, warehouse_id),
        qty_in_transit=get_qty_in_transit(db, product_id),
        warehouse_id=warehouse_id,
    )
