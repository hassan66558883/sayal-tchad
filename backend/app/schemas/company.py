from pydantic import BaseModel, ConfigDict


class BranchCreate(BaseModel):
    name: str
    code: str
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    manager_id: int | None = None


class BranchUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    manager_id: int | None = None
    active: bool | None = None


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    address: str | None
    city: str | None
    phone: str | None
    manager_id: int | None
    active: bool
