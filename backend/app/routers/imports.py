from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.import_ import IMPORT_STATE_ORDER, IMPORT_STATES, Container, Import
from app.models.purchase import PurchaseOrder
from app.models.user import User
from app.schemas.import_ import ImportCreate, ImportRead, ImportUpdate
from app.services.import_cost import apply_real_cost_to_products
from app.services.sequence import next_reference

PURCHASE_MANAGERS = ("achats", "direction_generale")

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.get("", response_model=list[ImportRead])
def list_imports(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Import).all()


@router.get("/{import_id}", response_model=ImportRead)
def read_import(import_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    record = db.get(Import, import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Importation introuvable.")
    return record


@router.post("", response_model=ImportRead, status_code=status.HTTP_201_CREATED)
def create_import(
    payload: ImportCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PURCHASE_MANAGERS)),
):
    order = db.get(PurchaseOrder, payload.purchase_order_id)
    if order is None or order.state != "commande":
        raise HTTPException(
            status_code=400, detail="L'importation requiert une commande d'achat confirmee (etat 'commande')."
        )
    if db.query(Import).filter(Import.purchase_order_id == payload.purchase_order_id).count():
        raise HTTPException(status_code=400, detail="Cette commande d'achat a deja une importation.")
    if payload.container_id is not None and db.get(Container, payload.container_id) is None:
        raise HTTPException(status_code=400, detail="Conteneur introuvable.")

    record = Import(
        purchase_order_id=payload.purchase_order_id,
        container_id=payload.container_id,
        bl_number=payload.bl_number,
        port=payload.port,
        state="nouveau",
    )
    record.reference = next_reference(db, code="import", prefix="IMP")
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{import_id}", response_model=ImportRead)
def update_import(
    import_id: int,
    payload: ImportUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PURCHASE_MANAGERS)),
):
    record = db.get(Import, import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Importation introuvable.")
    if record.state == "receptionne":
        raise HTTPException(status_code=400, detail="Une importation receptionnee ne peut plus etre modifiee.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.post("/{import_id}/advance", response_model=ImportRead)
def advance_import(
    import_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*PURCHASE_MANAGERS))
):
    record = db.get(Import, import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Importation introuvable.")
    current_index = IMPORT_STATE_ORDER[record.state]
    if current_index >= len(IMPORT_STATES) - 1:
        raise HTTPException(status_code=400, detail="Cette importation est deja receptionnee.")
    next_state = IMPORT_STATES[current_index + 1]
    record.state = next_state
    if next_state == "receptionne":
        apply_real_cost_to_products(db, record)
    db.commit()
    db.refresh(record)
    return record
