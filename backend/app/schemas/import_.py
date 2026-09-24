from datetime import date

from pydantic import BaseModel, ConfigDict


class ContainerCreate(BaseModel):
    number: str
    size: str | None = None
    notes: str | None = None


class ContainerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: str
    size: str | None
    notes: str | None


class ImportCreate(BaseModel):
    purchase_order_id: int
    container_id: int | None = None
    bl_number: str | None = None
    port: str | None = None


class ImportUpdate(BaseModel):
    container_id: int | None = None
    bl_number: str | None = None
    port: str | None = None
    transport_cost: float | None = None
    customs_cost: float | None = None
    transit_cost: float | None = None
    other_costs: float | None = None
    shipped_date: date | None = None
    arrival_date: date | None = None


class ImportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    purchase_order_id: int
    container_id: int | None
    state: str
    bl_number: str | None
    port: str | None
    transport_cost: float
    customs_cost: float
    transit_cost: float
    other_costs: float
    shipped_date: date | None
    arrival_date: date | None
