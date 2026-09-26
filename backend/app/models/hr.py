from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

LEAVE_TYPES = ["conge_paye", "maladie", "autre"]
LEAVE_STATES = ["en_attente", "approuvee", "refusee"]
PAYSLIP_STATES = ["draft", "validated"]


class Employee(Base, AuditedMixin):
    """Optionally linked to a user account (same pattern as Driver and
    SalesRep) so an employee can later see their own leave requests.
    """

    __tablename__ = "employees"
    __table_args__ = (CheckConstraint("base_salary >= 0", name="employee_base_salary_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    position: Mapped[str] = mapped_column(String(255))
    hire_date: Mapped[date] = mapped_column(Date)
    base_salary: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(default=True)

    user = relationship("User", foreign_keys=[user_id])
    branch = relationship("Branch")


class LeaveRequest(Base, AuditedMixin):
    """En_attente -> approuvee/refusee. A leave overlapping today counts
    toward the live "employees on leave today" figure
    (app/services/hr.py) - never a stored/cached headcount.
    """

    __tablename__ = "leave_requests"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="leave_request_end_after_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    leave_type: Mapped[str] = mapped_column(String(16), default="conge_paye")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(16), default="en_attente")

    employee = relationship("Employee")


class Payslip(Base, AuditedMixin):
    """Draft -> validated (final, like a confirmed payment). net_pay is
    never stored - always base_salary + bonuses - deductions, computed
    on every read (the property below), the same discipline used
    throughout this project for every derived figure.
    """

    __tablename__ = "payslips"
    __table_args__ = (
        CheckConstraint("bonuses >= 0", name="payslip_bonuses_non_negative"),
        CheckConstraint("deductions >= 0", name="payslip_deductions_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    base_salary: Mapped[float] = mapped_column(Float)
    bonuses: Mapped[float] = mapped_column(Float, default=0.0)
    deductions: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String(16), default="draft")
    payment_method: Mapped[str] = mapped_column(String(16), default="especes")
    cash_session_id: Mapped[int | None] = mapped_column(ForeignKey("cash_sessions.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank_accounts.id"))

    employee = relationship("Employee")
    cash_session = relationship("CashSession")
    bank_account = relationship("BankAccount")

    @property
    def net_pay(self) -> float:
        return self.base_salary + self.bonuses - self.deductions
