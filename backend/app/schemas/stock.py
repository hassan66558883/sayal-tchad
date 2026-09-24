from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class WarehouseCreate(BaseModel):
    name: str
    code: str


class WarehouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    active: bool


class StockLotCreate(BaseModel):
    product_id: int
    lot_number: str
    expiry_date: date | None = None


class StockLotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    lot_number: str
    expiry_date: date | None


class StockMoveCreate(BaseModel):
    move_type: str
    product_id: int
    qty: float
    source_warehouse_id: int | None = None
    dest_warehouse_id: int | None = None
    lot_id: int | None = None
    reason: str | None = None

    @field_validator("qty")
    @classmethod
    def qty_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("La quantite doit etre strictement positive.")
        return value


class StockMoveUpdate(BaseModel):
    """While draft, any field may change (subject to the same type/
    warehouse validation as creation). Once done, only reason may
    change - enforced in the router, mirroring the original write()
    override that made a validated move immutable except for its
    reason.
    """

    move_type: str | None = None
    product_id: int | None = None
    qty: float | None = None
    source_warehouse_id: int | None = None
    dest_warehouse_id: int | None = None
    lot_id: int | None = None
    reason: str | None = None

    @field_validator("qty")
    @classmethod
    def qty_must_be_positive(cls, value: float | None) -> float | None:
        if value is not None and value <= 0:
            raise ValueError("La quantite doit etre strictement positive.")
        return value


class StockMoveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    move_type: str
    product_id: int
    qty: float
    source_warehouse_id: int | None
    dest_warehouse_id: int | None
    lot_id: int | None
    state: str
    reason: str | None
    move_date: datetime


class StockInventoryLineCreate(BaseModel):
    product_id: int
    counted_qty: float


class StockInventoryLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    counted_qty: float
    theoretical_qty: float | None


class StockInventoryCreate(BaseModel):
    warehouse_id: int
    inventory_date: date
    lines: list[StockInventoryLineCreate] = []


class StockInventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    warehouse_id: int
    inventory_date: date
    state: str
    lines: list[StockInventoryLineRead] = []


class ProductStockRead(BaseModel):
    product_id: int
    qty_on_hand: float
    qty_in_transit: float
    warehouse_id: int | None = None
