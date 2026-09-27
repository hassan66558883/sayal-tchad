"""Cross-module summary reports, every figure computed live from real
rows for the requested period - never stored/cached, the same
discipline used throughout this project for every derived figure.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceLine, Payment
from app.models.product import Product
from app.models.sale import SaleOrder
from app.services.hr import get_active_employee_count, get_employees_on_leave, get_payroll_cost_total
from app.services.invoice import get_payment_summary


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


def get_sales_evolution(db: Session, period_start: date, period_end: date, granularity: str = "day") -> list[dict]:
    """Invoiced revenue grouped by day or by month, for the requested period."""
    trunc_unit = "month" if granularity == "month" else "day"
    bucket = func.date_trunc(trunc_unit, Invoice.invoice_date).label("bucket")
    rows = db.execute(
        select(bucket, func.coalesce(func.sum(Invoice.amount_total), 0.0), func.count(func.distinct(Invoice.id)))
        .where(
            Invoice.state == "validated",
            Invoice.move_type == "invoice",
            Invoice.invoice_date >= period_start,
            Invoice.invoice_date <= period_end,
        )
        .group_by(bucket)
        .order_by(bucket)
    ).all()
    return [
        {
            "period": (bucket_value.date() if hasattr(bucket_value, "date") else bucket_value).isoformat(),
            "invoiced_total": total,
            "invoice_count": count,
        }
        for bucket_value, total, count in rows
    ]


def get_sales_by_product(db: Session, period_start: date, period_end: date, limit: int = 10) -> list[dict]:
    rows = db.execute(
        select(
            Product.id,
            Product.name,
            func.coalesce(func.sum(InvoiceLine.qty), 0.0),
            func.coalesce(func.sum(InvoiceLine.qty * InvoiceLine.unit_price), 0.0),
        )
        .select_from(InvoiceLine)
        .join(Product, Product.id == InvoiceLine.product_id)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(
            Invoice.state == "validated",
            Invoice.move_type == "invoice",
            Invoice.invoice_date >= period_start,
            Invoice.invoice_date <= period_end,
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(InvoiceLine.qty * InvoiceLine.unit_price).desc())
        .limit(limit)
    ).all()
    return [{"product_id": r[0], "name": r[1], "qty": r[2], "revenue": r[3]} for r in rows]


def get_receivables_aging(db: Session) -> list[dict]:
    """Open (unpaid/partially paid) customer invoices, aged by days since invoice date.

    The system does not track a per-invoice due date, so "age" here means
    days elapsed since the invoice was issued, not days past a due date.
    """
    invoices = (
        db.query(Invoice).filter(Invoice.state == "validated", Invoice.move_type == "invoice").all()
    )
    today = date.today()
    rows = []
    for invoice in invoices:
        summary = get_payment_summary(db, invoice)
        if summary.amount_due <= 0:
            continue
        rows.append(
            {
                "invoice_id": invoice.id,
                "reference": invoice.reference,
                "customer_id": invoice.customer_id,
                "customer_name": invoice.customer.name if invoice.customer else None,
                "invoice_date": invoice.invoice_date.isoformat(),
                "amount_total": invoice.amount_total,
                "amount_paid": summary.amount_paid,
                "amount_due": summary.amount_due,
                "age_days": (today - invoice.invoice_date).days,
            }
        )
    rows.sort(key=lambda r: -r["age_days"])
    return rows
