from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin


class ProductCategory(Base, AuditedMixin):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32), unique=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent = relationship("ProductCategory", remote_side=[id])


class ProductBrand(Base, AuditedMixin):
    __tablename__ = "product_brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UomCategory(Base, AuditedMixin):
    __tablename__ = "uom_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    uoms = relationship("Uom", back_populates="category")


class Uom(Base, AuditedMixin):
    """A unit of measure within a category. factor is relative to the
    category's reference unit (is_reference=True, factor=1.0) - e.g. a
    "Sac de 50 kg" in the "Poids" category has factor=50 against the
    reference unit "Kilogramme" (factor=1). See
    app.services.uom.convert_qty for the conversion itself.
    """

    __tablename__ = "uoms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[int] = mapped_column(ForeignKey("uom_categories.id"))
    factor: Mapped[float] = mapped_column(Float, default=1.0)
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    category = relationship("UomCategory", back_populates="uoms")


class Product(Base, AuditedMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"))
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("product_brands.id"))
    uom_id: Mapped[int] = mapped_column(ForeignKey("uoms.id"))
    uom_po_id: Mapped[int | None] = mapped_column(ForeignKey("uoms.id"))
    purchase_price: Mapped[float] = mapped_column(Float, default=0.0)
    cost_price: Mapped[float] = mapped_column(Float, default=0.0)
    sale_price: Mapped[float] = mapped_column(Float, default=0.0)
    wholesale_price: Mapped[float] = mapped_column(Float, default=0.0)
    retail_price: Mapped[float] = mapped_column(Float, default=0.0)
    min_stock_qty: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    category = relationship("ProductCategory")
    brand = relationship("ProductBrand")
    uom = relationship("Uom", foreign_keys=[uom_id])
    uom_po = relationship("Uom", foreign_keys=[uom_po_id])
