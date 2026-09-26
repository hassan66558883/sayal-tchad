from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class FuelLogCreate(BaseModel):
    vehicle_id: int
    driver_id: int | None = None
    log_date: date
    odometer: float | None = None
    liters: float
    unit_price: float
    payment_method: str = "especes"
    cash_session_id: int | None = None
    bank_account_id: int | None = None

    @field_validator("liters")
    @classmethod
    def liters_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Le volume de carburant doit etre strictement positif.")
        return value

    @field_validator("unit_price")
    @classmethod
    def unit_price_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Le prix unitaire ne peut pas etre negatif.")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_must_be_valid(cls, value: str) -> str:
        if value not in ("especes", "banque"):
            raise ValueError("Mode de paiement invalide (especes ou banque).")
        return value


class FuelLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int
    driver_id: int | None
    log_date: date
    odometer: float | None
    liters: float
    unit_price: float
    total_cost: float
    payment_method: str
    cash_session_id: int | None
    bank_account_id: int | None


class VehicleMaintenanceCreate(BaseModel):
    vehicle_id: int
    maintenance_date: date
    description: str
    cost: float = 0.0
    payment_method: str = "especes"
    cash_session_id: int | None = None
    bank_account_id: int | None = None

    @field_validator("cost")
    @classmethod
    def cost_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Le cout ne peut pas etre negatif.")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_must_be_valid(cls, value: str) -> str:
        if value not in ("especes", "banque"):
            raise ValueError("Mode de paiement invalide (especes ou banque).")
        return value


class VehicleMaintenanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int
    maintenance_date: date
    description: str
    cost: float
    state: str
    payment_method: str
    cash_session_id: int | None
    bank_account_id: int | None


class VehicleDocumentCreate(BaseModel):
    vehicle_id: int
    document_type: str
    reference: str | None = None
    start_date: date
    end_date: date
    cost: float = 0.0

    @field_validator("document_type")
    @classmethod
    def document_type_must_be_valid(cls, value: str) -> str:
        if value not in ("assurance", "controle_technique", "vignette", "autre"):
            raise ValueError("Type de document invalide.")
        return value

    @field_validator("cost")
    @classmethod
    def cost_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Le cout ne peut pas etre negatif.")
        return value

    @model_validator(mode="after")
    def end_after_start(self) -> "VehicleDocumentCreate":
        if self.end_date < self.start_date:
            raise ValueError("La date de fin doit etre posterieure ou egale a la date de debut.")
        return self


class VehicleDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int
    document_type: str
    reference: str | None
    start_date: date
    end_date: date
    cost: float
