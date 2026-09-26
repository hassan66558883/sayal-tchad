from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DeliveryRouteCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    warehouse_id: int | None = None
    route_date: date


class DeliveryLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    ordered_qty: float
    delivered_qty: float


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    route_id: int
    sale_order_id: int
    state: str
    signature_data: str | None
    photo_url: str | None
    delivered_at: datetime | None
    gps_latitude: float | None
    gps_longitude: float | None
    issue_description: str | None
    lines: list[DeliveryLineRead] = []


class DeliveryRouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    driver_id: int
    vehicle_id: int
    warehouse_id: int | None
    route_date: date
    state: str
    deliveries: list[DeliveryRead] = []


class DeliveryCreate(BaseModel):
    route_id: int
    sale_order_id: int


class DeliveryLineConfirm(BaseModel):
    line_id: int
    delivered_qty: float


class DeliveryConfirm(BaseModel):
    lines: list[DeliveryLineConfirm]
    signature_data: str | None = None
    photo_url: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    issue_description: str | None = None
