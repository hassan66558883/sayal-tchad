from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.fleet_ops import FuelLog, VehicleDocument, VehicleMaintenance


def get_vehicle_fuel_cost_total(db: Session, vehicle_id: int) -> float:
    """Fuel cost is liters * unit_price per log, summed live - the same
    "never store a derived total" discipline used throughout this
    project (stock quantities, invoice/customer balances, cash/bank
    balances).
    """

    logs = db.query(FuelLog).filter(FuelLog.vehicle_id == vehicle_id).all()
    return sum(log.total_cost for log in logs)


def get_vehicle_maintenance_cost_total(db: Session, vehicle_id: int) -> float:
    return db.execute(
        select(func.coalesce(func.sum(VehicleMaintenance.cost), 0.0)).where(
            VehicleMaintenance.vehicle_id == vehicle_id, VehicleMaintenance.state == "terminee"
        )
    ).scalar_one()


def list_expiring_documents(db: Session, within_days: int = 30) -> list[VehicleDocument]:
    today = date.today()
    horizon = today + timedelta(days=within_days)
    return (
        db.query(VehicleDocument)
        .filter(VehicleDocument.end_date >= today, VehicleDocument.end_date <= horizon)
        .order_by(VehicleDocument.end_date)
        .all()
    )
