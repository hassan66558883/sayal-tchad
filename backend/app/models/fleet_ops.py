from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditedMixin

MAINTENANCE_STATES = ["planifiee", "terminee", "annulee"]
DOCUMENT_TYPES = ["assurance", "controle_technique", "vignette", "autre"]


class FuelLog(Base, AuditedMixin):
    __tablename__ = "fuel_logs"
    __table_args__ = (
        CheckConstraint("liters > 0", name="fuel_log_liters_positive"),
        CheckConstraint("unit_price >= 0", name="fuel_log_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"))
    log_date: Mapped[date] = mapped_column(Date)
    odometer: Mapped[float | None] = mapped_column(Float)
    liters: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)
    payment_method: Mapped[str] = mapped_column(String(16), default="especes")
    cash_session_id: Mapped[int | None] = mapped_column(ForeignKey("cash_sessions.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank_accounts.id"))

    vehicle = relationship("Vehicle")
    driver = relationship("Driver")
    cash_session = relationship("CashSession")
    bank_account = relationship("BankAccount")

    @property
    def total_cost(self) -> float:
        return self.liters * self.unit_price


class VehicleMaintenance(Base, AuditedMixin):
    __tablename__ = "vehicle_maintenances"
    __table_args__ = (CheckConstraint("cost >= 0", name="vehicle_maintenance_cost_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    maintenance_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(255))
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String(16), default="planifiee")
    payment_method: Mapped[str] = mapped_column(String(16), default="especes")
    cash_session_id: Mapped[int | None] = mapped_column(ForeignKey("cash_sessions.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank_accounts.id"))

    vehicle = relationship("Vehicle")
    cash_session = relationship("CashSession")
    bank_account = relationship("BankAccount")


class VehicleDocument(Base, AuditedMixin):
    """Insurance, technical control (controle technique), road tax
    (vignette) - anything on a vehicle with a validity window, so a
    single query can surface everything expiring soon.
    """

    __tablename__ = "vehicle_documents"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="vehicle_document_end_after_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(32))
    reference: Mapped[str | None] = mapped_column(String(64))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    cost: Mapped[float] = mapped_column(Float, default=0.0)

    vehicle = relationship("Vehicle")
