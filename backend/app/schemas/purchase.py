from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


class PurchaseOrderLineCreate(BaseModel):
    product_id: int
    qty: float
    unit_price: float

    @field_validator("qty")
    @classmethod
    def qty_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("La quantite doit etre strictement positive.")
        return value

    @field_validator("unit_price")
    @classmethod
    def unit_price_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Le prix unitaire ne peut pas etre negatif.")
        return value


class PurchaseOrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    qty: float
    unit_price: float
    subtotal: float


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    branch_id: int | None = None
    order_date: date
    lines: list[PurchaseOrderLineCreate] = []


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    supplier_id: int
    branch_id: int | None
    order_date: date
    state: str
    amount_total: float
    lines: list[PurchaseOrderLineRead] = []
