from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.product import Product
from app.models.stock import StockInventory, StockInventoryLine, StockMove, Warehouse
from app.models.user import User
from app.schemas.stock import StockInventoryCreate, StockInventoryLineCreate, StockInventoryRead
from app.services.sequence import next_reference
from app.services.stock import get_qty_on_hand

STOCK_MANAGERS = ("stock", "direction_generale")

router = APIRouter(prefix="/api/stock-inventories", tags=["stock"])


@router.get("", response_model=list[StockInventoryRead])
def list_inventories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(StockInventory).all()


@router.post("", response_model=StockInventoryRead, status_code=status.HTTP_201_CREATED)
def create_inventory(
    payload: StockInventoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STOCK_MANAGERS)),
):
    if db.get(Warehouse, payload.warehouse_id) is None:
        raise HTTPException(status_code=400, detail="Entrepot introuvable.")
    inventory = StockInventory(warehouse_id=payload.warehouse_id, inventory_date=payload.inventory_date, state="draft")
    inventory.reference = next_reference(db, code="stock_inventory", prefix="INV")
    for line_payload in payload.lines:
        if db.get(Product, line_payload.product_id) is None:
            raise HTTPException(status_code=400, detail="Produit introuvable dans une ligne.")
        inventory.lines.append(StockInventoryLine(**line_payload.model_dump()))
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory


@router.post("/{inventory_id}/lines", response_model=StockInventoryRead)
def add_inventory_line(
    inventory_id: int,
    payload: StockInventoryLineCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STOCK_MANAGERS)),
):
    inventory = db.get(StockInventory, inventory_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventaire introuvable.")
    if inventory.state != "draft":
        raise HTTPException(status_code=400, detail="Impossible d'ajouter une ligne a un inventaire valide.")
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=400, detail="Produit introuvable.")
    inventory.lines.append(StockInventoryLine(**payload.model_dump()))
    db.commit()
    db.refresh(inventory)
    return inventory


@router.post("/{inventory_id}/validate", response_model=StockInventoryRead)
def validate_inventory(
    inventory_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*STOCK_MANAGERS))
):
    inventory = db.get(StockInventory, inventory_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventaire introuvable.")
    if inventory.state != "draft":
        raise HTTPException(status_code=400, detail="Cet inventaire est deja valide.")

    for line in inventory.lines:
        theoretical = get_qty_on_hand(db, line.product_id, inventory.warehouse_id)
        line.theoretical_qty = theoretical
        delta = line.counted_qty - theoretical
        if delta > 0:
            db.add(
                StockMove(
                    move_type="adjustment_in",
                    product_id=line.product_id,
                    qty=delta,
                    dest_warehouse_id=inventory.warehouse_id,
                    state="done",
                    reason=f"Ecart inventaire {inventory.reference}",
                )
            )
        elif delta < 0:
            db.add(
                StockMove(
                    move_type="adjustment_out",
                    product_id=line.product_id,
                    qty=abs(delta),
                    source_warehouse_id=inventory.warehouse_id,
                    state="done",
                    reason=f"Ecart inventaire {inventory.reference}",
                )
            )
    inventory.state = "validated"
    db.commit()
    db.refresh(inventory)
    return inventory
