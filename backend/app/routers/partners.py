from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.partner import Partner
from app.models.user import User
from app.schemas.partner import PartnerCreate, PartnerRead, PartnerUpdate
from app.services.rbac import scope_by_branch
from app.services.sequence import next_reference

PARTNER_MANAGERS = ("ventes", "achats", "direction_generale")

router = APIRouter(prefix="/api/partners", tags=["partners"])


@router.get("", response_model=list[PartnerRead])
def list_partners(
    is_customer: bool | None = Query(default=None),
    is_supplier: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Partner).where(Partner.active.is_(True))
    if is_customer is not None:
        stmt = stmt.where(Partner.is_customer.is_(is_customer))
    if is_supplier is not None:
        stmt = stmt.where(Partner.is_supplier.is_(is_supplier))
    stmt = scope_by_branch(stmt, Partner.branch_id, current_user)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=PartnerRead, status_code=status.HTTP_201_CREATED)
def create_partner(
    payload: PartnerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PARTNER_MANAGERS)),
):
    if not payload.is_customer and not payload.is_supplier:
        raise HTTPException(status_code=400, detail="Un tiers doit etre client et/ou fournisseur.")
    partner = Partner(**payload.model_dump())
    partner.reference = next_reference(db, code="partner", prefix="TRS")
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.patch("/{partner_id}", response_model=PartnerRead)
def update_partner(
    partner_id: int,
    payload: PartnerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PARTNER_MANAGERS)),
):
    partner = db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Tiers introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(partner, field, value)
    db.commit()
    db.refresh(partner)
    return partner
