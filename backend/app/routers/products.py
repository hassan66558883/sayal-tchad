from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.product import Product, Uom
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.sequence import next_reference

CATALOG_MANAGERS = ("achats", "stock", "direction_generale")

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Product).filter(Product.active.is_(True)).all()


@router.get("/{product_id}", response_model=ProductRead)
def read_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CATALOG_MANAGERS)),
):
    if db.get(Uom, payload.uom_id) is None:
        raise HTTPException(status_code=400, detail="Unite de stockage introuvable.")
    if payload.barcode and db.query(Product).filter(Product.barcode == payload.barcode).count():
        raise HTTPException(status_code=400, detail="Ce code-barres existe deja.")
    product = Product(**payload.model_dump())
    product.reference = next_reference(db, code="product", prefix="PRD")
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CATALOG_MANAGERS)),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product
