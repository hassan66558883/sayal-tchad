from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


class InvoiceLineCreate(BaseModel):
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


class InvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    qty: float
    unit_price: float
    subtotal: float


class InvoiceCreateFromOrder(BaseModel):
    sale_order_id: int


class CreditNoteCreate(BaseModel):
    origin_invoice_id: int
    invoice_date: date
    lines: list[InvoiceLineCreate] = []


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    move_type: str
    sale_order_id: int | None
    origin_invoice_id: int | None
    customer_id: int
    invoice_date: date
    state: str
    amount_total: float
    amount_paid: float
    amount_due: float
    payment_state: str
    lines: list[InvoiceLineRead] = []


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_date: date

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Le montant doit etre strictement positif.")
        return value


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    invoice_id: int
    amount: float
    payment_date: date
    state: str
