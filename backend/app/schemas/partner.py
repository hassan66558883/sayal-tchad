from pydantic import BaseModel, ConfigDict, field_validator

from app.models.partner import CUSTOMER_TYPES


class PartnerCreate(BaseModel):
    name: str
    is_customer: bool = False
    is_supplier: bool = False
    customer_type: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    branch_id: int | None = None
    salesperson_id: int | None = None
    credit_limit: float = 0.0

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, value: str | None) -> str | None:
        if value is not None and value not in CUSTOMER_TYPES:
            raise ValueError(f"customer_type doit etre l'un de : {', '.join(CUSTOMER_TYPES)}")
        return value


class PartnerUpdate(BaseModel):
    name: str | None = None
    customer_type: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    branch_id: int | None = None
    salesperson_id: int | None = None
    credit_limit: float | None = None
    active: bool | None = None


class PartnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    name: str
    is_customer: bool
    is_supplier: bool
    customer_type: str | None
    phone: str | None
    email: str | None
    address: str | None
    branch_id: int | None
    salesperson_id: int | None
    credit_limit: float
    active: bool
