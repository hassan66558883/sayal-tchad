from pydantic import BaseModel, ConfigDict


class ProductCategoryCreate(BaseModel):
    name: str
    code: str
    parent_id: int | None = None


class ProductCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    parent_id: int | None
    active: bool


class ProductBrandCreate(BaseModel):
    name: str
    code: str


class ProductBrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    active: bool


class UomCategoryCreate(BaseModel):
    name: str


class UomCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class UomCreate(BaseModel):
    name: str
    category_id: int
    factor: float = 1.0
    is_reference: bool = False


class UomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category_id: int
    factor: float
    is_reference: bool
    active: bool


class ProductCreate(BaseModel):
    name: str
    barcode: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    uom_id: int
    uom_po_id: int | None = None
    purchase_price: float = 0.0
    cost_price: float = 0.0
    sale_price: float = 0.0
    wholesale_price: float = 0.0
    retail_price: float = 0.0
    min_stock_qty: float = 0.0


class ProductUpdate(BaseModel):
    name: str | None = None
    barcode: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    purchase_price: float | None = None
    cost_price: float | None = None
    sale_price: float | None = None
    wholesale_price: float | None = None
    retail_price: float | None = None
    min_stock_qty: float | None = None
    active: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    name: str
    barcode: str | None
    category_id: int | None
    brand_id: int | None
    uom_id: int
    uom_po_id: int | None
    purchase_price: float
    cost_price: float
    sale_price: float
    wholesale_price: float
    retail_price: float
    min_stock_qty: float
    active: bool
