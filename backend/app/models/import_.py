from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

IMPORT_STATES = ["nouveau", "expedie", "arrive", "douane", "receptionne"]
IMPORT_STATE_ORDER = {state: index for index, state in enumerate(IMPORT_STATES)}


class Container(Base, AuditedMixin):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(32), unique=True)
    size: Mapped[str | None] = mapped_column(String(16))
    notes: Mapped[str | None] = mapped_column(String(255))


class Import(Base, AuditedMixin):
    """Import workflow bridging a confirmed PurchaseOrder to real landed
    cost on each product, mirroring the original design: real_cost_total
    (purchase amount + transport/customs/transit/other) is allocated pro
    rata across the order's lines the moment the import reaches
    "receptionne", and written directly onto Product.cost_price - no
    weighted-average-with-existing-stock logic (there is no stock ledger
    yet; that is Phase 4).
    """

    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), unique=True)
    container_id: Mapped[int | None] = mapped_column(ForeignKey("containers.id"))
    state: Mapped[str] = mapped_column(String(16), default="nouveau")
    bl_number: Mapped[str | None] = mapped_column(String(64))
    port: Mapped[str | None] = mapped_column(String(128))
    transport_cost: Mapped[float] = mapped_column(Float, default=0.0)
    customs_cost: Mapped[float] = mapped_column(Float, default=0.0)
    transit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    other_costs: Mapped[float] = mapped_column(Float, default=0.0)
    shipped_date: Mapped[date | None] = mapped_column(Date)
    arrival_date: Mapped[date | None] = mapped_column(Date)

    purchase_order = relationship("PurchaseOrder", back_populates="import_")
    container = relationship("Container")

    @property
    def extra_costs_total(self) -> float:
        return self.transport_cost + self.customs_cost + self.transit_cost + self.other_costs
