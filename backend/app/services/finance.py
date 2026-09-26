"""Live balances for cash sessions and bank accounts: always summed on
demand from real, confirmed/validated rows (customer payments, supplier
payments, expenses, fuel logs, completed vehicle maintenances, manual
bank transactions) - never a stored/cached running total, the same
anti-pattern avoidance applied throughout this project (Phase 4's stock
quantities, Phase 5's invoice/customer balances).
"""

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finance import BankAccount, BankTransaction, CashSession, Expense, SupplierPayment
from app.models.fleet_ops import FuelLog, VehicleMaintenance
from app.models.invoice import Payment


def validate_payment_method_target(
    db: Session,
    payment_method: str,
    cash_session_id: int | None,
    bank_account_id: int | None,
    require_target: bool = False,
) -> None:
    """Shared guard for every place money changes hands (customer
    payments, supplier payments, expenses). For customer/supplier
    payments, tagging a movement to a cash session or bank account is
    optional (so the pre-existing payment flows from Phase 5 keep
    working untracked) - but when a caller does tag one, it must be the
    right kind and in a usable state. Expenses (a new Phase 7 concept,
    and the higher-risk direction - money leaving) pass
    require_target=True: every cash/bank expense must trace to a real
    session/account, so a cash/bank balance can never silently miss
    money that actually left.
    """

    if payment_method not in ("especes", "banque"):
        raise HTTPException(status_code=400, detail="Mode de paiement invalide.")

    if payment_method == "especes":
        if bank_account_id is not None:
            raise HTTPException(status_code=400, detail="Un paiement en especes ne peut pas cibler un compte bancaire.")
        if cash_session_id is None:
            if require_target:
                raise HTTPException(status_code=400, detail="Une session de caisse ouverte est requise pour un paiement en especes.")
        else:
            session = db.get(CashSession, cash_session_id)
            if session is None or session.state != "open":
                raise HTTPException(status_code=400, detail="La session de caisse doit exister et etre ouverte.")
    else:
        if cash_session_id is not None:
            raise HTTPException(status_code=400, detail="Un paiement bancaire ne peut pas cibler une session de caisse.")
        if bank_account_id is None:
            if require_target:
                raise HTTPException(status_code=400, detail="Un compte bancaire est requis pour un paiement par banque.")
        else:
            account = db.get(BankAccount, bank_account_id)
            if account is None or not account.active:
                raise HTTPException(status_code=400, detail="Le compte bancaire doit exister et etre actif.")


def get_cash_session_balance(db: Session, session: CashSession) -> float:
    cash_in = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.cash_session_id == session.id,
            Payment.payment_method == "especes",
            Payment.state == "confirmed",
        )
    ).scalar_one()
    supplier_out = db.execute(
        select(func.coalesce(func.sum(SupplierPayment.amount), 0.0)).where(
            SupplierPayment.cash_session_id == session.id,
            SupplierPayment.payment_method == "especes",
            SupplierPayment.state == "confirmed",
        )
    ).scalar_one()
    expenses_out = db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.cash_session_id == session.id,
            Expense.payment_method == "especes",
            Expense.state == "validated",
        )
    ).scalar_one()
    fuel_out = db.execute(
        select(func.coalesce(func.sum(FuelLog.liters * FuelLog.unit_price), 0.0)).where(
            FuelLog.cash_session_id == session.id, FuelLog.payment_method == "especes"
        )
    ).scalar_one()
    maintenance_out = db.execute(
        select(func.coalesce(func.sum(VehicleMaintenance.cost), 0.0)).where(
            VehicleMaintenance.cash_session_id == session.id,
            VehicleMaintenance.payment_method == "especes",
            VehicleMaintenance.state == "terminee",
        )
    ).scalar_one()
    return session.opening_balance + cash_in - supplier_out - expenses_out - fuel_out - maintenance_out


def get_bank_account_balance(db: Session, account_id: int, opening_balance: float) -> float:
    bank_in = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.bank_account_id == account_id,
            Payment.payment_method == "banque",
            Payment.state == "confirmed",
        )
    ).scalar_one()
    supplier_out = db.execute(
        select(func.coalesce(func.sum(SupplierPayment.amount), 0.0)).where(
            SupplierPayment.bank_account_id == account_id,
            SupplierPayment.payment_method == "banque",
            SupplierPayment.state == "confirmed",
        )
    ).scalar_one()
    expenses_out = db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.bank_account_id == account_id,
            Expense.payment_method == "banque",
            Expense.state == "validated",
        )
    ).scalar_one()
    manual_in = db.execute(
        select(func.coalesce(func.sum(BankTransaction.amount), 0.0)).where(
            BankTransaction.bank_account_id == account_id, BankTransaction.movement_type == "in"
        )
    ).scalar_one()
    manual_out = db.execute(
        select(func.coalesce(func.sum(BankTransaction.amount), 0.0)).where(
            BankTransaction.bank_account_id == account_id, BankTransaction.movement_type == "out"
        )
    ).scalar_one()
    fuel_out = db.execute(
        select(func.coalesce(func.sum(FuelLog.liters * FuelLog.unit_price), 0.0)).where(
            FuelLog.bank_account_id == account_id, FuelLog.payment_method == "banque"
        )
    ).scalar_one()
    maintenance_out = db.execute(
        select(func.coalesce(func.sum(VehicleMaintenance.cost), 0.0)).where(
            VehicleMaintenance.bank_account_id == account_id,
            VehicleMaintenance.payment_method == "banque",
            VehicleMaintenance.state == "terminee",
        )
    ).scalar_one()
    return (
        opening_balance
        + bank_in
        - supplier_out
        - expenses_out
        + manual_in
        - manual_out
        - fuel_out
        - maintenance_out
    )
