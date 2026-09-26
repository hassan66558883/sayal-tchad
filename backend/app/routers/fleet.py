from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.fleet import Driver, Vehicle
from app.models.user import User
from app.schemas.fleet import DriverCreate, DriverRead, VehicleCreate, VehicleRead

LOGISTICS_MANAGERS = ("logistique", "direction_generale")

router = APIRouter(prefix="/api", tags=["fleet"])


@router.get("/vehicles", response_model=list[VehicleRead])
def list_vehicles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Vehicle).filter(Vehicle.active.is_(True)).all()


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    if db.query(Vehicle).filter(Vehicle.plate_number == payload.plate_number).count():
        raise HTTPException(status_code=400, detail="Cette immatriculation existe deja.")
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/drivers", response_model=list[DriverRead])
def list_drivers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Driver).filter(Driver.active.is_(True)).all()


@router.post("/drivers", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    if payload.user_id is not None:
        if db.get(User, payload.user_id) is None:
            raise HTTPException(status_code=400, detail="Utilisateur introuvable.")
        if db.query(Driver).filter(Driver.user_id == payload.user_id).count():
            raise HTTPException(status_code=400, detail="Cet utilisateur est deja lie a un chauffeur.")
    driver = Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver
