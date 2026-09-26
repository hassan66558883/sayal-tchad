"""Cross-module summary reports, every figure computed live from real
rows for the requested period - never stored/cached, the same
discipline used throughout this project for every derived figure.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, Payment
from app.models.sale import SaleOrder
from app.services.hr import get_active_employee_count, get_employees_on_leave, get_payroll_cost_total


def get_sales_summary(db: Session, period_start: date, period_end: date) -> dict[str, float]:
    total_confirmed_sales = db.execute(
        select(func.coalesce(func.sum(SaleOrder.amount_total), 0.0)).where(
            SaleOrder.state.in_(("commande", "terminee")),
            SaleOrder.order_date >= period_start,
            SaleOrder.order_date <= period_end,
        )
    ).scalar_one()

    invoiced = db.execute(
        select(func.coalesce(func.sum(Invoice.amount_total), 0.0)).where(
            Invoice.state == "validated",
            Invoice.move_type == "invoice",
            Invoice.invoice_date >= period_start,
            Invoice.invoice_date <= period_end,
        )
    ).scalar_one()
    credit_notes = db.execute(
        select(func.coalesce(func.sum(Invoice.amount_total), 0.0)).where(
            Invoice.state == "validated",
            Invoice.move_type == "credit_note",
            Invoice.invoice_date >= period_start,
            Invoice.invoice_date <= period_end,
        )
    ).scalar_one()

    collected = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.state == "confirmed",
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
        )
    ).scalar_one()

    return {
        "total_confirmed_sales": total_confirmed_sales,
        "total_invoiced": invoiced - credit_notes,
        "total_collected": collected,
    }


def get_hr_summary(db: Session, period_start: date, period_end: date) -> dict[str, float]:
    return {
        "active_employee_count": get_active_employee_count(db),
        "on_leave_today_count": len(get_employees_on_leave(db, date.today())),
        "payroll_cost": get_payroll_cost_total(db, period_start, period_end),
    }
