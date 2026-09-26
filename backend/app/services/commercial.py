"""Commissions and target achievement, always computed live from real
confirmed/completed sale orders - never a stored/cached figure, the
same discipline used throughout this project for every derived amount
(stock quantities, invoice/customer balances, cash/bank balances).
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.commercial import SalesRep, SalesTarget
from app.models.sale import SaleOrder

COUNTED_STATES = ("commande", "terminee")


def get_sales_rep_sales_total(db: Session, sales_rep_id: int, period_start: date, period_end: date) -> float:
    return db.execute(
        select(func.coalesce(func.sum(SaleOrder.amount_total), 0.0)).where(
            SaleOrder.sales_rep_id == sales_rep_id,
            SaleOrder.state.in_(COUNTED_STATES),
            SaleOrder.order_date >= period_start,
            SaleOrder.order_date <= period_end,
        )
    ).scalar_one()


def get_sales_rep_commission(db: Session, sales_rep: SalesRep, period_start: date, period_end: date) -> float:
    total = get_sales_rep_sales_total(db, sales_rep.id, period_start, period_end)
    return total * sales_rep.commission_rate / 100


def get_target_achievement(db: Session, target: SalesTarget) -> dict[str, float | None]:
    achieved = get_sales_rep_sales_total(db, target.sales_rep_id, target.period_start, target.period_end)
    percent = (achieved / target.target_amount * 100) if target.target_amount > 0 else None
    return {"achieved_amount": achieved, "achievement_percent": percent}
