"""A small notification feed built from real, already-tracked alert
conditions (low stock, expiring vehicle documents, pending leave
requests, pending payment confirmations, old open receivables) -
nothing here is stored, it is recomputed on every request. Available
to any authenticated user, unlike the executive dashboard which is
restricted to direction_generale.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models.finance import Expense
from app.models.hr import LeaveRequest
from app.models.invoice import Payment
from app.models.product import Product
from app.services.fleet_ops import list_expiring_documents
from app.services.reports import get_receivables_aging
from app.services.stock import get_qty_on_hand


def get_notifications(db: Session) -> list[dict]:
    notifications: list[dict] = []

    low_stock_count = 0
    for product in db.query(Product).filter(Product.active.is_(True), Product.min_stock_qty > 0).all():
        if get_qty_on_hand(db, product.id) < product.min_stock_qty:
            low_stock_count += 1
    if low_stock_count:
        notifications.append(
            {
                "id": "low-stock",
                "type": "stock",
                "severity": "warning",
                "title": "Alertes stock bas",
                "message": f"{low_stock_count} produit(s) sous le seuil minimum.",
                "path": "/products",
            }
        )

    expiring = list_expiring_documents(db, 30)
    if expiring:
        notifications.append(
            {
                "id": "expiring-documents",
                "type": "fleet",
                "severity": "warning",
                "title": "Documents vehicule a renouveler",
                "message": f"{len(expiring)} document(s) expirant sous 30 jours.",
                "path": "/fleet-operations",
            }
        )

    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.state == "en_attente").count()
    if pending_leaves:
        notifications.append(
            {
                "id": "pending-leaves",
                "type": "hr",
                "severity": "info",
                "title": "Demandes de conge en attente",
                "message": f"{pending_leaves} demande(s) a traiter.",
                "path": "/hr",
            }
        )

    pending_payments = db.query(Payment).filter(Payment.state == "draft").count()
    if pending_payments:
        notifications.append(
            {
                "id": "pending-payments",
                "type": "finance",
                "severity": "info",
                "title": "Paiements a confirmer",
                "message": f"{pending_payments} paiement(s) client en attente de confirmation.",
                "path": "/invoices",
            }
        )

    pending_expenses = db.query(Expense).filter(Expense.state == "draft").count()
    if pending_expenses:
        notifications.append(
            {
                "id": "pending-expenses",
                "type": "finance",
                "severity": "info",
                "title": "Depenses a valider",
                "message": f"{pending_expenses} depense(s) en brouillon.",
                "path": "/cash-registers",
            }
        )

    old_receivables = [r for r in get_receivables_aging(db) if r["age_days"] > 60]
    if old_receivables:
        notifications.append(
            {
                "id": "old-receivables",
                "type": "finance",
                "severity": "danger",
                "title": "Creances anciennes",
                "message": f"{len(old_receivables)} facture(s) ouverte(s) depuis plus de 60 jours.",
                "path": "/receivables",
            }
        )

    return notifications
