from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


class SaleOrderLineCreate(BaseModel):
    product_id: int
    qty: float
    unit_price: float
    discount_percent: float = 0.0

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

    @field_validator("discount_percent")
    @classmethod
    def discount_must_be_in_range(cls, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("La remise doit etre comprise entre 0 et 100.")
        return value


class SaleOrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    qty: float
    unit_price: float
    discount_percent: float
    subtotal: float


class SaleOrderCreate(BaseModel):
    customer_id: int
    branch_id: int | None = None
    order_date: date
    lines: list[SaleOrderLineCreate] = []


class SaleOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    customer_id: int
    branch_id: int | None
    order_date: date
    state: str
    amount_total: float
    lines: list[SaleOrderLineRead] = []
