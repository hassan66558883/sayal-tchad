"""Executive dashboard: a single aggregate of live figures already
computed elsewhere in the codebase (sales, HR, cash/bank, stock,
fleet, distribution) - nothing here is stored or cached, it is
recomputed on every request from the same services each module already
uses, so the dashboard can never drift from the screens it summarizes.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.delivery import DeliveryRoute
from app.models.finance import BankAccount, CashSession, SupplierInvoice
from app.models.fleet_ops import VehicleDocument
from app.models.hr import LeaveRequest
from app.models.invoice import Invoice
from app.models.product import Product
from app.services.finance import get_bank_account_balance, get_cash_session_balance
from app.services.fleet_ops import list_expiring_documents
from app.services.hr import get_active_employee_count, get_employees_on_leave, get_payroll_cost_total
from app.services.invoice import get_payment_summary
from app.services.reports import get_sales_summary
from app.services.stock import get_qty_on_hand
from app.services.supplier_invoice import get_supplier_payment_summary


def get_low_stock_products(db: Session) -> list[dict]:
    products = db.query(Product).filter(Product.active.is_(True), Product.min_stock_qty > 0).all()
    alerts = []
    for product in products:
        qty_on_hand = get_qty_on_hand(db, product.id)
        if qty_on_hand < product.min_stock_qty:
            alerts.append(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "qty_on_hand": qty_on_hand,
                    "min_stock_qty": product.min_stock_qty,
                }
            )
    return alerts


def get_total_receivables(db: Session) -> float:
    invoices = db.query(Invoice).filter(Invoice.state == "validated").all()
    total = 0.0
    for invoice in invoices:
        sign = 1 if invoice.move_type == "invoice" else -1
        total += sign * get_payment_summary(db, invoice).amount_due
    return total


def get_total_payables(db: Session) -> float:
    invoices = db.query(SupplierInvoice).filter(SupplierInvoice.state == "validated").all()
    total = 0.0
    for invoice in invoices:
        sign = 1 if invoice.move_type == "bill" else -1
        total += sign * get_supplier_payment_summary(db, invoice).amount_due
    return total


def get_cash_overview(db: Session) -> list[dict]:
    sessions = db.query(CashSession).filter(CashSession.state == "open").all()
    return [
        {
            "register_id": s.register_id,
            "session_id": s.id,
            "balance": get_cash_session_balance(db, s),
        }
        for s in sessions
    ]


def get_bank_overview(db: Session) -> list[dict]:
    accounts = db.query(BankAccount).filter(BankAccount.active.is_(True)).all()
    return [
        {"account_id": a.id, "name": a.name, "balance": get_bank_account_balance(db, a.id, a.opening_balance)}
        for a in accounts
    ]


def get_open_delivery_route_count(db: Session) -> int:
    return db.execute(
        select(func.count()).select_from(DeliveryRoute).where(
            DeliveryRoute.state.in_(("planifiee", "chargee", "en_livraison"))
        )
    ).scalar_one()


def get_dashboard_summary(db: Session, period_start: date, period_end: date) -> dict:
    return {
        "sales": get_sales_summary(db, period_start, period_end),
        "hr": {
            "active_employee_count": get_active_employee_count(db),
            "on_leave_today_count": len(get_employees_on_leave(db, date.today())),
            "payroll_cost": get_payroll_cost_total(db, period_start, period_end),
            "pending_leave_requests": db.query(LeaveRequest).filter(LeaveRequest.state == "en_attente").count(),
        },
        "finance": {
            "total_receivables": get_total_receivables(db),
            "total_payables": get_total_payables(db),
            "cash_sessions": get_cash_overview(db),
            "bank_accounts": get_bank_overview(db),
        },
        "stock": {"low_stock_products": get_low_stock_products(db)},
        "fleet": {"expiring_documents": [_document_to_dict(d) for d in list_expiring_documents(db, 30)]},
        "distribution": {"open_delivery_routes": get_open_delivery_route_count(db)},
    }


def _document_to_dict(document: VehicleDocument) -> dict:
    return {
        "vehicle_id": document.vehicle_id,
        "document_type": document.document_type,
        "end_date": document.end_date.isoformat(),
    }
