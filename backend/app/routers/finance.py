from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.finance import BankAccount, BankTransaction, CashRegister, CashSession, Expense
from app.models.user import User
from app.schemas.finance import (
    BankAccountCreate,
    BankAccountRead,
    BankTransactionCreate,
    BankTransactionRead,
    CashRegisterCreate,
    CashRegisterRead,
    CashSessionClose,
    CashSessionOpen,
    CashSessionRead,
    ExpenseCreate,
    ExpenseRead,
)
from app.services.finance import get_bank_account_balance, get_cash_session_balance, validate_payment_method_target
from app.services.sequence import next_reference

FINANCE_MANAGERS = ("comptable", "direction_generale")
CASHIER_ROLES = ("caissier", "comptable", "direction_generale")

router = APIRouter(prefix="/api", tags=["finance"])


def _cash_session_to_read(db: Session, session: CashSession) -> CashSessionRead:
    computed = get_cash_session_balance(db, session)
    variance = None if session.closing_balance is None else session.closing_balance - computed
    return CashSessionRead(
        id=session.id,
        register_id=session.register_id,
        state=session.state,
        opening_balance=session.opening_balance,
        closing_balance=session.closing_balance,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        computed_balance=computed,
        variance=variance,
    )


def _bank_account_to_read(db: Session, account: BankAccount) -> BankAccountRead:
    return BankAccountRead(
        id=account.id,
        name=account.name,
        bank_name=account.bank_name,
        account_number=account.account_number,
        opening_balance=account.opening_balance,
        active=account.active,
        balance=get_bank_account_balance(db, account.id, account.opening_balance),
    )


@router.get("/cash-registers", response_model=list[CashRegisterRead])
def list_cash_registers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(CashRegister).filter(CashRegister.active.is_(True)).all()


@router.post("/cash-registers", response_model=CashRegisterRead, status_code=status.HTTP_201_CREATED)
def create_cash_register(
    payload: CashRegisterCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*FINANCE_MANAGERS))
):
    if db.query(CashRegister).filter(CashRegister.code == payload.code).count():
        raise HTTPException(status_code=400, detail="Ce code de caisse existe deja.")
    register = CashRegister(**payload.model_dump())
    db.add(register)
    db.commit()
    db.refresh(register)
    return register


@router.get("/cash-sessions", response_model=list[CashSessionRead])
def list_cash_sessions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_cash_session_to_read(db, s) for s in db.query(CashSession).all()]


@router.post("/cash-sessions", response_model=CashSessionRead, status_code=status.HTTP_201_CREATED)
def open_cash_session(
    payload: CashSessionOpen, db: Session = Depends(get_db), _: User = Depends(require_roles(*CASHIER_ROLES))
):
    register = db.get(CashRegister, payload.register_id)
    if register is None:
        raise HTTPException(status_code=400, detail="Caisse introuvable.")
    if db.query(CashSession).filter(CashSession.register_id == register.id, CashSession.state == "open").count():
        raise HTTPException(status_code=400, detail="Cette caisse a deja une session ouverte.")
    session = CashSession(register_id=register.id, opening_balance=payload.opening_balance, state="open")
    db.add(session)
    db.commit()
    db.refresh(session)
    return _cash_session_to_read(db, session)


@router.post("/cash-sessions/{session_id}/close", response_model=CashSessionRead)
def close_cash_session(
    session_id: int,
    payload: CashSessionClose,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*CASHIER_ROLES)),
):
    session = db.get(CashSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session de caisse introuvable.")
    if session.state != "open":
        raise HTTPException(status_code=400, detail="Cette session est deja cloturee.")
    session.closing_balance = payload.closing_balance
    session.closed_at = datetime.now(timezone.utc)
    session.state = "closed"
    db.commit()
    db.refresh(session)
    return _cash_session_to_read(db, session)


@router.get("/bank-accounts", response_model=list[BankAccountRead])
def list_bank_accounts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_bank_account_to_read(db, a) for a in db.query(BankAccount).filter(BankAccount.active.is_(True)).all()]


@router.post("/bank-accounts", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    payload: BankAccountCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*FINANCE_MANAGERS))
):
    if db.query(BankAccount).filter(BankAccount.account_number == payload.account_number).count():
        raise HTTPException(status_code=400, detail="Ce numero de compte existe deja.")
    account = BankAccount(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return _bank_account_to_read(db, account)


@router.get("/bank-transactions", response_model=list[BankTransactionRead])
def list_bank_transactions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(BankTransaction).all()


@router.post("/bank-transactions", response_model=BankTransactionRead, status_code=status.HTTP_201_CREATED)
def create_bank_transaction(
    payload: BankTransactionCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*FINANCE_MANAGERS))
):
    account = db.get(BankAccount, payload.bank_account_id)
    if account is None:
        raise HTTPException(status_code=400, detail="Compte bancaire introuvable.")
    transaction = BankTransaction(**payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Expense).all()


@router.post("/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*CASHIER_ROLES))
):
    validate_payment_method_target(
        db, payload.payment_method, payload.cash_session_id, payload.bank_account_id, require_target=True
    )
    expense = Expense(**payload.model_dump(), state="draft")
    expense.reference = next_reference(db, code="expense", prefix="DEP")
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.post("/expenses/{expense_id}/validate", response_model=ExpenseRead)
def validate_expense(
    expense_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*FINANCE_MANAGERS))
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Depense introuvable.")
    if expense.state != "draft":
        raise HTTPException(status_code=400, detail="Seule une depense en brouillon peut etre validee.")
    expense.state = "validated"
    db.commit()
    db.refresh(expense)
    return expense


@router.post("/expenses/{expense_id}/cancel", response_model=ExpenseRead)
def cancel_expense(
    expense_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*FINANCE_MANAGERS))
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Depense introuvable.")
    if expense.state != "draft":
        raise HTTPException(status_code=400, detail="Une depense validee est immuable et ne peut pas etre annulee.")
    expense.state = "cancelled"
    db.commit()
    db.refresh(expense)
    return expense
