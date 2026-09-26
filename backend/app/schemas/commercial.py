from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SalesRepCreate(BaseModel):
    name: str
    user_id: int | None = None
    commission_rate: float = 0.0

    @field_validator("commission_rate")
    @classmethod
    def commission_rate_must_be_in_range(cls, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("Le taux de commission doit etre compris entre 0 et 100.")
        return value


class SalesRepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    user_id: int | None
    commission_rate: float
    active: bool


class SalesTargetCreate(BaseModel):
    sales_rep_id: int
    period_start: date
    period_end: date
    target_amount: float

    @field_validator("target_amount")
    @classmethod
    def target_amount_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("L'objectif doit etre strictement positif.")
        return value

    @model_validator(mode="after")
    def end_after_start(self) -> "SalesTargetCreate":
        if self.period_end < self.period_start:
            raise ValueError("La date de fin doit etre posterieure ou egale a la date de debut.")
        return self


class SalesTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sales_rep_id: int
    period_start: date
    period_end: date
    target_amount: float
    achieved_amount: float
    achievement_percent: float | None
