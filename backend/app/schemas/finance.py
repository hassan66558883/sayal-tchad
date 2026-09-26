from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CashRegisterCreate(BaseModel):
    name: str
    code: str
    branch_id: int | None = None


class CashRegisterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    branch_id: int | None
    active: bool


class CashSessionOpen(BaseModel):
    register_id: int
    opening_balance: float = 0.0


class CashSessionClose(BaseModel):
    closing_balance: float


class CashSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    register_id: int
    state: str
    opening_balance: float
    closing_balance: float | None
    opened_at: datetime
    closed_at: datetime | None
    computed_balance: float
    variance: float | None


class BankAccountCreate(BaseModel):
    name: str
    bank_name: str
    account_number: str
    opening_balance: float = 0.0


class BankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    bank_name: str
    account_number: str
    opening_balance: float
    active: bool
    balance: float


class BankTransactionCreate(BaseModel):
    bank_account_id: int
    movement_type: str
    amount: float
    reason: str | None = None
    transaction_date: date

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Le montant doit etre strictement positif.")
        return value

    @field_validator("movement_type")
    @classmethod
    def movement_type_must_be_valid(cls, value: str) -> str:
        if value not in ("in", "out"):
            raise ValueError("Type de mouvement invalide (in ou out).")
        return value


class BankTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bank_account_id: int
    movement_type: str
    amount: float
    reason: str | None
    transaction_date: date


class ExpenseCreate(BaseModel):
    category: str
    description: str | None = None
    amount: float
    expense_date: date
    branch_id: int | None = None
    payment_method: str = "especes"
    cash_session_id: int | None = None
    bank_account_id: int | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Le montant doit etre strictement positif.")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_must_be_valid(cls, value: str) -> str:
        if value not in ("especes", "banque"):
            raise ValueError("Mode de paiement invalide (especes ou banque).")
        return value


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    category: str
    description: str | None
    amount: float
    expense_date: date
    branch_id: int | None
    state: str
    payment_method: str
    cash_session_id: int | None
    bank_account_id: int | None


class SupplierInvoiceLineCreate(BaseModel):
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


class SupplierInvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    qty: float
    unit_price: float
    subtotal: float


class SupplierInvoiceCreateFromOrder(BaseModel):
    purchase_order_id: int


class SupplierDebitNoteCreate(BaseModel):
    origin_invoice_id: int
    invoice_date: date
    lines: list[SupplierInvoiceLineCreate] = []


class SupplierInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    move_type: str
    purchase_order_id: int | None
    origin_invoice_id: int | None
    supplier_id: int
    invoice_date: date
    state: str
    amount_total: float
    amount_paid: float
    amount_due: float
    payment_state: str
    lines: list[SupplierInvoiceLineRead] = []


class SupplierPaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_date: date
    payment_method: str = "especes"
    cash_session_id: int | None = None
    bank_account_id: int | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Le montant doit etre strictement positif.")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_must_be_valid(cls, value: str) -> str:
        if value not in ("especes", "banque"):
            raise ValueError("Mode de paiement invalide (especes ou banque).")
        return value


class SupplierPaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    invoice_id: int
    amount: float
    payment_date: date
    state: str
    payment_method: str
    cash_session_id: int | None
    bank_account_id: int | None
