from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.hr import Employee, LeaveRequest, Payslip
from app.models.user import User
from app.schemas.hr import (
    EmployeeCreate,
    EmployeeRead,
    LeaveRequestCreate,
    LeaveRequestRead,
    PayslipCreate,
    PayslipRead,
)
from app.services.finance import validate_payment_method_target
from app.services.hr_scope import get_own_employee, is_rh_manager, scope_leave_requests
from app.services.sequence import next_reference

RH_MANAGERS = ("rh", "direction_generale")

router = APIRouter(prefix="/api", tags=["hr"])


@router.get("/employees", response_model=list[EmployeeRead])
def list_employees(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Employee).filter(Employee.active.is_(True)).all()


@router.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*RH_MANAGERS))
):
    if payload.user_id is not None:
        if db.get(User, payload.user_id) is None:
            raise HTTPException(status_code=400, detail="Utilisateur introuvable.")
        if db.query(Employee).filter(Employee.user_id == payload.user_id).count():
            raise HTTPException(status_code=400, detail="Cet utilisateur est deja lie a un employe.")
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/leave-requests", response_model=list[LeaveRequestRead])
def list_leave_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = scope_leave_requests(db, current_user)
    return db.execute(stmt).scalars().unique().all()


@router.post("/leave-requests", response_model=LeaveRequestRead, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    payload: LeaveRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if db.get(Employee, payload.employee_id) is None:
        raise HTTPException(status_code=400, detail="Employe introuvable.")
    if not is_rh_manager(current_user):
        own_employee = get_own_employee(db, current_user)
        if own_employee is None or own_employee.id != payload.employee_id:
            raise HTTPException(
                status_code=403, detail="Vous ne pouvez creer une demande de conge que pour vous-meme."
            )
    request = LeaveRequest(**payload.model_dump(), state="en_attente")
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.post("/leave-requests/{request_id}/approve", response_model=LeaveRequestRead)
def approve_leave_request(
    request_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*RH_MANAGERS))
):
    leave_request = db.get(LeaveRequest, request_id)
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Demande de conge introuvable.")
    if leave_request.state != "en_attente":
        raise HTTPException(status_code=400, detail="Seule une demande en attente peut etre approuvee.")
    leave_request.state = "approuvee"
    db.commit()
    db.refresh(leave_request)
    return leave_request


@router.post("/leave-requests/{request_id}/reject", response_model=LeaveRequestRead)
def reject_leave_request(
    request_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*RH_MANAGERS))
):
    leave_request = db.get(LeaveRequest, request_id)
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Demande de conge introuvable.")
    if leave_request.state != "en_attente":
        raise HTTPException(status_code=400, detail="Seule une demande en attente peut etre refusee.")
    leave_request.state = "refusee"
    db.commit()
    db.refresh(leave_request)
    return leave_request


@router.get("/payslips", response_model=list[PayslipRead])
def list_payslips(db: Session = Depends(get_db), _: User = Depends(require_roles(*RH_MANAGERS))):
    return db.query(Payslip).all()


@router.post("/payslips", response_model=PayslipRead, status_code=status.HTTP_201_CREATED)
def create_payslip(
    payload: PayslipCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*RH_MANAGERS))
):
    if db.get(Employee, payload.employee_id) is None:
        raise HTTPException(status_code=400, detail="Employe introuvable.")
    payslip = Payslip(**payload.model_dump(), state="draft")
    payslip.reference = next_reference(db, code="payslip", prefix="BUL")
    db.add(payslip)
    db.commit()
    db.refresh(payslip)
    return payslip


@router.post("/payslips/{payslip_id}/validate", response_model=PayslipRead)
def validate_payslip(payslip_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*RH_MANAGERS))):
    payslip = db.get(Payslip, payslip_id)
    if payslip is None:
        raise HTTPException(status_code=404, detail="Bulletin de paie introuvable.")
    if payslip.state != "draft":
        raise HTTPException(status_code=400, detail="Seul un bulletin en brouillon peut etre valide.")
    validate_payment_method_target(
        db, payslip.payment_method, payslip.cash_session_id, payslip.bank_account_id, require_target=True
    )
    payslip.state = "validated"
    db.commit()
    db.refresh(payslip)
    return payslip
