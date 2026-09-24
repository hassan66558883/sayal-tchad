from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.product import Product
from app.models.stock import StockLot, Warehouse
from app.models.user import User
from app.schemas.stock import StockLotCreate, StockLotRead, WarehouseCreate, WarehouseRead

STOCK_MANAGERS = ("stock", "direction_generale")

router = APIRouter(prefix="/api", tags=["stock"])


@router.get("/warehouses", response_model=list[WarehouseRead])
def list_warehouses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Warehouse).filter(Warehouse.active.is_(True)).all()


@router.post("/warehouses", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STOCK_MANAGERS)),
):
    if db.query(Warehouse).filter(Warehouse.code == payload.code).count():
        raise HTTPException(status_code=400, detail="Ce code d'entrepot existe deja.")
    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/stock-lots", response_model=list[StockLotRead])
def list_stock_lots(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(StockLot).all()


@router.post("/stock-lots", response_model=StockLotRead, status_code=status.HTTP_201_CREATED)
def create_stock_lot(
    payload: StockLotCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STOCK_MANAGERS)),
):
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=400, detail="Produit introuvable.")
    lot = StockLot(**payload.model_dump())
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot
