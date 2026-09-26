from datetime import date

from sqlalchemy.orm import Session

from app.models.hr import Employee, LeaveRequest, Payslip


def get_active_employee_count(db: Session) -> int:
    return db.query(Employee).filter(Employee.active.is_(True)).count()


def get_employees_on_leave(db: Session, on_date: date) -> list[LeaveRequest]:
    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.state == "approuvee",
            LeaveRequest.start_date <= on_date,
            LeaveRequest.end_date >= on_date,
        )
        .all()
    )


def get_payroll_cost_total(db: Session, period_start: date, period_end: date) -> float:
    """Payroll cost is always summed live from validated payslips'
    real net_pay (never a stored/cached total), the same discipline
    used throughout this project for every derived figure.
    """

    payslips = (
        db.query(Payslip)
        .filter(Payslip.state == "validated", Payslip.period_start >= period_start, Payslip.period_end <= period_end)
        .all()
    )
    return sum(p.net_pay for p in payslips)
