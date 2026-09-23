from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    label: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    active: bool
    is_superuser: bool
    roles: list[RoleRead] = []


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_codes: list[str] = []
