from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

MOVE_TYPES = ["in", "out", "transfer", "adjustment_in", "adjustment_out"]
MOVE_TYPES_REQUIRING_SOURCE = {"out", "transfer", "adjustment_out"}
MOVE_TYPES_REQUIRING_DEST = {"in", "transfer", "adjustment_in"}


class Warehouse(Base, AuditedMixin):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockLot(Base, AuditedMixin):
    __tablename__ = "stock_lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    lot_number: Mapped[str] = mapped_column(String(64))
    expiry_date: Mapped[date | None] = mapped_column(Date)

    product = relationship("Product")


class StockMove(Base, AuditedMixin):
    """Draft -> done, immutable once done (enforced in the router, which
    only allows editing the "reason" field afterward) - the same
    "keeps a complete, tamper-evident history" requirement the original
    design mentions.
    """

    __tablename__ = "stock_moves"
    __table_args__ = (CheckConstraint("qty > 0", name="stock_move_qty_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    move_type: Mapped[str] = mapped_column(String(16))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    source_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    dest_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("stock_lots.id"))
    state: Mapped[str] = mapped_column(String(16), default="draft")
    reason: Mapped[str | None] = mapped_column(String(255))
    move_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    dest_warehouse = relationship("Warehouse", foreign_keys=[dest_warehouse_id])
    lot = relationship("StockLot")


class StockInventory(Base, AuditedMixin):
    __tablename__ = "stock_inventories"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    inventory_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="draft")

    warehouse = relationship("Warehouse")
    lines = relationship("StockInventoryLine", back_populates="inventory", cascade="all, delete-orphan")


class StockInventoryLine(Base):
    __tablename__ = "stock_inventory_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("stock_inventories.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    counted_qty: Mapped[float] = mapped_column(Float)
    theoretical_qty: Mapped[float | None] = mapped_column(Float)

    inventory = relationship("StockInventory", back_populates="lines")
    product = relationship("Product")
