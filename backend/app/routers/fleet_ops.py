from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.fleet import Vehicle
from app.models.fleet_ops import FuelLog, VehicleDocument, VehicleMaintenance
from app.models.user import User
from app.schemas.fleet_ops import (
    FuelLogCreate,
    FuelLogRead,
    VehicleDocumentCreate,
    VehicleDocumentRead,
    VehicleMaintenanceCreate,
    VehicleMaintenanceRead,
)
from app.services.finance import validate_payment_method_target
from app.services.fleet_ops import get_vehicle_fuel_cost_total, get_vehicle_maintenance_cost_total, list_expiring_documents

FLEET_MANAGERS = ("logistique", "direction_generale")

router = APIRouter(prefix="/api", tags=["fleet-ops"])


@router.get("/fuel-logs", response_model=list[FuelLogRead])
def list_fuel_logs(
    vehicle_id: int | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    query = db.query(FuelLog)
    if vehicle_id is not None:
        query = query.filter(FuelLog.vehicle_id == vehicle_id)
    return query.all()


@router.post("/fuel-logs", response_model=FuelLogRead, status_code=status.HTTP_201_CREATED)
def create_fuel_log(
    payload: FuelLogCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*FLEET_MANAGERS))
):
    if db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status_code=400, detail="Vehicule introuvable.")
    validate_payment_method_target(
        db, payload.payment_method, payload.cash_session_id, payload.bank_account_id, require_target=True
    )
    log = FuelLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/vehicles/{vehicle_id}/fuel-cost")
def read_vehicle_fuel_cost(
    vehicle_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> dict[str, float]:
    if db.get(Vehicle, vehicle_id) is None:
        raise HTTPException(status_code=404, detail="Vehicule introuvable.")
    return {"total_fuel_cost": get_vehicle_fuel_cost_total(db, vehicle_id)}


@router.get("/vehicle-maintenances", response_model=list[VehicleMaintenanceRead])
def list_vehicle_maintenances(
    vehicle_id: int | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    query = db.query(VehicleMaintenance)
    if vehicle_id is not None:
        query = query.filter(VehicleMaintenance.vehicle_id == vehicle_id)
    return query.all()


@router.post("/vehicle-maintenances", response_model=VehicleMaintenanceRead, status_code=status.HTTP_201_CREATED)
def create_vehicle_maintenance(
    payload: VehicleMaintenanceCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*FLEET_MANAGERS))
):
    if db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status_code=400, detail="Vehicule introuvable.")
    if payload.cost > 0:
        validate_payment_method_target(
            db, payload.payment_method, payload.cash_session_id, payload.bank_account_id, require_target=True
        )
    maintenance = VehicleMaintenance(**payload.model_dump(), state="planifiee")
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance


@router.post("/vehicle-maintenances/{maintenance_id}/complete", response_model=VehicleMaintenanceRead)
def complete_vehicle_maintenance(
    maintenance_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*FLEET_MANAGERS))
):
    maintenance = db.get(VehicleMaintenance, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Entretien introuvable.")
    if maintenance.state != "planifiee":
        raise HTTPException(status_code=400, detail="Seul un entretien planifie peut etre termine.")
    maintenance.state = "terminee"
    db.commit()
    db.refresh(maintenance)
    return maintenance


@router.post("/vehicle-maintenances/{maintenance_id}/cancel", response_model=VehicleMaintenanceRead)
def cancel_vehicle_maintenance(
    maintenance_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*FLEET_MANAGERS))
):
    maintenance = db.get(VehicleMaintenance, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Entretien introuvable.")
    if maintenance.state != "planifiee":
        raise HTTPException(status_code=400, detail="Seul un entretien planifie peut etre annule.")
    maintenance.state = "annulee"
    db.commit()
    db.refresh(maintenance)
    return maintenance


@router.get("/vehicles/{vehicle_id}/maintenance-cost")
def read_vehicle_maintenance_cost(
    vehicle_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> dict[str, float]:
    if db.get(Vehicle, vehicle_id) is None:
        raise HTTPException(status_code=404, detail="Vehicule introuvable.")
    return {"total_maintenance_cost": get_vehicle_maintenance_cost_total(db, vehicle_id)}


@router.get("/vehicle-documents", response_model=list[VehicleDocumentRead])
def list_vehicle_documents(
    vehicle_id: int | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    query = db.query(VehicleDocument)
    if vehicle_id is not None:
        query = query.filter(VehicleDocument.vehicle_id == vehicle_id)
    return query.all()


@router.get("/vehicle-documents/expiring", response_model=list[VehicleDocumentRead])
def read_expiring_documents(
    within_days: int = Query(default=30), db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return list_expiring_documents(db, within_days)


@router.post("/vehicle-documents", response_model=VehicleDocumentRead, status_code=status.HTTP_201_CREATED)
def create_vehicle_document(
    payload: VehicleDocumentCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*FLEET_MANAGERS))
):
    if db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status_code=400, detail="Vehicule introuvable.")
    document = VehicleDocument(**payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
