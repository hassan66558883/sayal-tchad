from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

ROUTE_STATES = ["planifiee", "chargee", "en_livraison", "livree", "cloturee"]
DELIVERY_STATES = ["planifiee", "chargee", "en_livraison", "livree", "partielle", "probleme"]
DELIVERY_TERMINAL_STATES = {"livree", "partielle", "probleme"}


class DeliveryRoute(Base, AuditedMixin):
    """Planifiee -> Chargee -> En livraison -> Livree -> Cloturee. Loading
    (action_charger) and starting (action_demarrer) a route cascades the
    same transition onto every delivery it carries, so a delivery can
    never be confirmed before its route says it is out for delivery.
    """

    __tablename__ = "delivery_routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    route_date: Mapped[date] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(16), default="planifiee")

    driver = relationship("Driver")
    vehicle = relationship("Vehicle")
    warehouse = relationship("Warehouse")
    deliveries = relationship("Delivery", back_populates="route", cascade="all, delete-orphan")


class Delivery(Base, AuditedMixin):
    """One delivery per confirmed sale order. Confirming it (with a
    signature, or an issue report when it fails) records the proof of
    delivery and - when its route has a loading warehouse - creates the
    real (already-done) outbound stock move for whatever was actually
    delivered, never for what was merely ordered.
    """

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("delivery_routes.id"))
    sale_order_id: Mapped[int] = mapped_column(ForeignKey("sale_orders.id"), unique=True)
    state: Mapped[str] = mapped_column(String(16), default="planifiee")
    signature_data: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(512))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gps_latitude: Mapped[float | None] = mapped_column(Float)
    gps_longitude: Mapped[float | None] = mapped_column(Float)
    issue_description: Mapped[str | None] = mapped_column(Text)

    route = relationship("DeliveryRoute", back_populates="deliveries")
    sale_order = relationship("SaleOrder")
    lines = relationship("DeliveryLine", back_populates="delivery", cascade="all, delete-orphan")


class DeliveryLine(Base):
    __tablename__ = "delivery_lines"
    __table_args__ = (
        CheckConstraint("ordered_qty > 0", name="delivery_line_ordered_qty_positive"),
        CheckConstraint("delivered_qty >= 0", name="delivery_line_delivered_qty_non_negative"),
        CheckConstraint("delivered_qty <= ordered_qty", name="delivery_line_delivered_not_over_ordered"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_id: Mapped[int] = mapped_column(ForeignKey("deliveries.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    ordered_qty: Mapped[float] = mapped_column(Float)
    delivered_qty: Mapped[float] = mapped_column(Float, default=0.0)

    delivery = relationship("Delivery", back_populates="lines")
    product = relationship("Product")
