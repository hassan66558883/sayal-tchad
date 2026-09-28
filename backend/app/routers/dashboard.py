from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User
from app.services.dashboard import get_dashboard_summary
from app.services.reports import get_receivables_aging, get_sales_by_product, get_sales_evolution

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def read_dashboard_summary(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
) -> dict:
    return get_dashboard_summary(db, period_start, period_end)


@router.get("/sales-evolution")
def read_sales_evolution(
    period_start: date,
    period_end: date,
    granularity: str = "day",
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
) -> list[dict]:
    return get_sales_evolution(db, period_start, period_end, granularity)


@router.get("/sales-by-product")
def read_sales_by_product(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
) -> list[dict]:
    return get_sales_by_product(db, period_start, period_end)


@router.get("/receivables-aging")
def read_receivables_aging(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
) -> list[dict]:
    return get_receivables_aging(db)
