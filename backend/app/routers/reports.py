from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User
from app.services.reports import get_hr_summary, get_sales_summary

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/sales-summary")
def read_sales_summary(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale", "comptable", "ventes")),
) -> dict[str, float]:
    return get_sales_summary(db, period_start, period_end)


@router.get("/hr-summary")
def read_hr_summary(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale", "rh")),
) -> dict[str, float]:
    return get_hr_summary(db, period_start, period_end)
