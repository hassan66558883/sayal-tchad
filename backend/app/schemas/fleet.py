from pydantic import BaseModel, ConfigDict


class VehicleCreate(BaseModel):
    name: str
    plate_number: str


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    plate_number: str
    active: bool


class DriverCreate(BaseModel):
    name: str
    user_id: int | None = None


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    user_id: int | None
    active: bool
