from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def read_dashboard_summary(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
) -> dict:
    return get_dashboard_summary(db, period_start, period_end)
