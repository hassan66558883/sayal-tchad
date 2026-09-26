from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class EmployeeCreate(BaseModel):
    name: str
    user_id: int | None = None
    branch_id: int | None = None
    position: str
    hire_date: date
    base_salary: float = 0.0

    @field_validator("base_salary")
    @classmethod
    def base_salary_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Le salaire de base ne peut pas etre negatif.")
        return value


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    user_id: int | None
    branch_id: int | None
    position: str
    hire_date: date
    base_salary: float
    active: bool


class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: str = "conge_paye"
    start_date: date
    end_date: date
    reason: str | None = None

    @field_validator("leave_type")
    @classmethod
    def leave_type_must_be_valid(cls, value: str) -> str:
        if value not in ("conge_paye", "maladie", "autre"):
            raise ValueError("Type de conge invalide.")
        return value

    @model_validator(mode="after")
    def end_after_start(self) -> "LeaveRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("La date de fin doit etre posterieure ou egale a la date de debut.")
        return self


class LeaveRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None
    state: str


class PayslipCreate(BaseModel):
    employee_id: int
    period_start: date
    period_end: date
    base_salary: float
    bonuses: float = 0.0
    deductions: float = 0.0
    payment_method: str = "especes"
    cash_session_id: int | None = None
    bank_account_id: int | None = None

    @field_validator("bonuses", "deductions")
    @classmethod
    def must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Ce montant ne peut pas etre negatif.")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_must_be_valid(cls, value: str) -> str:
        if value not in ("especes", "banque"):
            raise ValueError("Mode de paiement invalide (especes ou banque).")
        return value

    @model_validator(mode="after")
    def end_after_start(self) -> "PayslipCreate":
        if self.period_end < self.period_start:
            raise ValueError("La date de fin doit etre posterieure ou egale a la date de debut.")
        return self


class PayslipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    employee_id: int
    period_start: date
    period_end: date
    base_salary: float
    bonuses: float
    deductions: float
    net_pay: float
    state: str
    payment_method: str
    cash_session_id: int | None
    bank_account_id: int | None
