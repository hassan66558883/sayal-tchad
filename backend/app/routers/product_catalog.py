from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.product import ProductBrand, ProductCategory, Uom, UomCategory
from app.models.user import User
from app.schemas.product import (
    ProductBrandCreate,
    ProductBrandRead,
    ProductCategoryCreate,
    ProductCategoryRead,
    UomCategoryCreate,
    UomCategoryRead,
    UomCreate,
    UomRead,
)

CATALOG_MANAGERS = ("achats", "stock", "direction_generale")

router = APIRouter(prefix="/api", tags=["product-catalog"])


@router.get("/product-categories", response_model=list[ProductCategoryRead])
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ProductCategory).filter(ProductCategory.active.is_(True)).all()


@router.post("/product-categories", response_model=ProductCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CATALOG_MANAGERS)),
):
    if db.query(ProductCategory).filter(ProductCategory.code == payload.code).count():
        raise HTTPException(status_code=400, detail="Ce code de categorie existe deja.")
    category = ProductCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/product-brands", response_model=list[ProductBrandRead])
def list_brands(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ProductBrand).filter(ProductBrand.active.is_(True)).all()


@router.post("/product-brands", response_model=ProductBrandRead, status_code=status.HTTP_201_CREATED)
def create_brand(
    payload: ProductBrandCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CATALOG_MANAGERS)),
):
    if db.query(ProductBrand).filter(ProductBrand.code == payload.code).count():
        raise HTTPException(status_code=400, detail="Ce code de marque existe deja.")
    brand = ProductBrand(**payload.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/uom-categories", response_model=list[UomCategoryRead])
def list_uom_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(UomCategory).all()


@router.post("/uom-categories", response_model=UomCategoryRead, status_code=status.HTTP_201_CREATED)
def create_uom_category(
    payload: UomCategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CATALOG_MANAGERS)),
):
    category = UomCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/uoms", response_model=list[UomRead])
def list_uoms(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Uom).filter(Uom.active.is_(True)).all()


@router.post("/uoms", response_model=UomRead, status_code=status.HTTP_201_CREATED)
def create_uom(
    payload: UomCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CATALOG_MANAGERS)),
):
    category = db.get(UomCategory, payload.category_id)
    if category is None:
        raise HTTPException(status_code=400, detail="Categorie d'unite introuvable.")
    uom = Uom(**payload.model_dump())
    db.add(uom)
    db.commit()
    db.refresh(uom)
    return uom
