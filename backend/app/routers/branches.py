from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.company import Branch
from app.models.user import User
from app.schemas.company import BranchCreate, BranchRead, BranchUpdate
from app.services.company import get_default_company
from app.services.rbac import scope_by_branch

router = APIRouter(prefix="/api/branches", tags=["branches"])


@router.get("", response_model=list[BranchRead])
def list_branches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Branch).where(Branch.active.is_(True))
    stmt = scope_by_branch(stmt, Branch.id, current_user)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
):
    if db.query(Branch).filter(Branch.code == payload.code).count():
        raise HTTPException(status_code=400, detail="Ce code d'agence existe deja.")
    branch = Branch(**payload.model_dump())
    branch.company_id = get_default_company(db).id
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.patch("/{branch_id}", response_model=BranchRead)
def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
):
    branch = db.get(Branch, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Agence introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)
    db.commit()
    db.refresh(branch)
    return branch
