"""Row-level scoping for leave requests, mirroring
app.services.driver_scope: a plain user (no RH/direction role) linked to
an Employee record via user_id sees only their own leave requests -
"Mes conges" - and nothing at all without a linked employee record
(secure-by-default).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hr import Employee, LeaveRequest
from app.models.user import User

RH_ROLES = {"rh", "direction_generale"}


def is_rh_manager(user: User) -> bool:
    if user.is_superuser:
        return True
    role_codes = {r.code for r in user.roles}
    return bool(role_codes & RH_ROLES)


def get_own_employee(db: Session, user: User) -> Employee | None:
    return db.execute(select(Employee).where(Employee.user_id == user.id)).scalar_one_or_none()


def scope_leave_requests(db: Session, user: User):
    """Returns a SQLAlchemy Select for leave requests visible to this
    user: everything for an RH manager, only their own linked employee's
    requests otherwise, or none at all if they have no linked employee.
    """

    stmt = select(LeaveRequest)
    if is_rh_manager(user):
        return stmt
    employee = get_own_employee(db, user)
    if employee is None:
        return stmt.where(LeaveRequest.id.in_([]))
    return stmt.where(LeaveRequest.employee_id == employee.id)
