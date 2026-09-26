from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.commercial import SalesRep, SalesTarget
from app.models.user import User
from app.schemas.commercial import SalesRepCreate, SalesRepRead, SalesTargetCreate, SalesTargetRead
from app.services.commercial import get_sales_rep_commission, get_target_achievement

COMMERCIAL_MANAGERS = ("direction_generale",)

router = APIRouter(prefix="/api", tags=["commercial"])


def _target_to_read(db: Session, target: SalesTarget) -> SalesTargetRead:
    achievement = get_target_achievement(db, target)
    return SalesTargetRead(
        id=target.id,
        sales_rep_id=target.sales_rep_id,
        period_start=target.period_start,
        period_end=target.period_end,
        target_amount=target.target_amount,
        achieved_amount=achievement["achieved_amount"],
        achievement_percent=achievement["achievement_percent"],
    )


@router.get("/sales-reps", response_model=list[SalesRepRead])
def list_sales_reps(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(SalesRep).filter(SalesRep.active.is_(True)).all()


@router.post("/sales-reps", response_model=SalesRepRead, status_code=status.HTTP_201_CREATED)
def create_sales_rep(
    payload: SalesRepCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*COMMERCIAL_MANAGERS))
):
    if payload.user_id is not None:
        if db.get(User, payload.user_id) is None:
            raise HTTPException(status_code=400, detail="Utilisateur introuvable.")
        if db.query(SalesRep).filter(SalesRep.user_id == payload.user_id).count():
            raise HTTPException(status_code=400, detail="Cet utilisateur est deja lie a un commercial.")
    rep = SalesRep(**payload.model_dump())
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return rep


@router.get("/sales-reps/{rep_id}/commission")
def read_sales_rep_commission(
    rep_id: int,
    period_start: str,
    period_end: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, float]:
    rep = db.get(SalesRep, rep_id)
    if rep is None:
        raise HTTPException(status_code=404, detail="Commercial introuvable.")
    commission = get_sales_rep_commission(
        db, rep, date.fromisoformat(period_start), date.fromisoformat(period_end)
    )
    return {"commission": commission}


@router.get("/sales-targets", response_model=list[SalesTargetRead])
def list_sales_targets(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_target_to_read(db, t) for t in db.query(SalesTarget).all()]


@router.post("/sales-targets", response_model=SalesTargetRead, status_code=status.HTTP_201_CREATED)
def create_sales_target(
    payload: SalesTargetCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*COMMERCIAL_MANAGERS))
):
    if db.get(SalesRep, payload.sales_rep_id) is None:
        raise HTTPException(status_code=400, detail="Commercial introuvable.")
    target = SalesTarget(**payload.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)
    return _target_to_read(db, target)
