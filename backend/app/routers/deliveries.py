from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.delivery import Delivery, DeliveryLine, DeliveryRoute
from app.models.fleet import Driver, Vehicle
from app.models.sale import SaleOrder
from app.models.stock import Warehouse
from app.models.user import User
from app.schemas.delivery import (
    DeliveryConfirm,
    DeliveryCreate,
    DeliveryRead,
    DeliveryRouteCreate,
    DeliveryRouteRead,
)
from app.services.delivery import close_route, confirm_delivery, finish_route, load_route, route_can_finish, start_route
from app.services.driver_scope import is_driver_restricted, scope_deliveries_by_driver, scope_routes_by_driver
from app.services.sequence import next_reference

LOGISTICS_MANAGERS = ("logistique", "direction_generale")
DELIVERY_CONFIRMERS = ("logistique", "direction_generale", "chauffeur")

router = APIRouter(prefix="/api", tags=["deliveries"])


@router.get("/delivery-routes", response_model=list[DeliveryRouteRead])
def list_routes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(DeliveryRoute)
    stmt = scope_routes_by_driver(stmt, db, current_user)
    return db.execute(stmt).scalars().unique().all()


@router.get("/delivery-routes/{route_id}", response_model=DeliveryRouteRead)
def read_route(route_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    route = db.get(DeliveryRoute, route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Tournee introuvable.")
    return route


@router.post("/delivery-routes", response_model=DeliveryRouteRead, status_code=status.HTTP_201_CREATED)
def create_route(
    payload: DeliveryRouteCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    if db.get(Driver, payload.driver_id) is None:
        raise HTTPException(status_code=400, detail="Chauffeur introuvable.")
    if db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status_code=400, detail="Vehicule introuvable.")
    if payload.warehouse_id is not None and db.get(Warehouse, payload.warehouse_id) is None:
        raise HTTPException(status_code=400, detail="Entrepot introuvable.")

    route = DeliveryRoute(
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        warehouse_id=payload.warehouse_id,
        route_date=payload.route_date,
        state="planifiee",
    )
    route.reference = next_reference(db, code="delivery_route", prefix="TRN")
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


@router.post("/delivery-routes/{route_id}/load", response_model=DeliveryRouteRead)
def load_route_endpoint(
    route_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    route = db.get(DeliveryRoute, route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Tournee introuvable.")
    if route.state != "planifiee":
        raise HTTPException(status_code=400, detail="Seule une tournee planifiee peut etre chargee.")
    load_route(db, route)
    db.commit()
    db.refresh(route)
    return route


@router.post("/delivery-routes/{route_id}/start", response_model=DeliveryRouteRead)
def start_route_endpoint(
    route_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    route = db.get(DeliveryRoute, route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Tournee introuvable.")
    if route.state != "chargee":
        raise HTTPException(status_code=400, detail="Seule une tournee chargee peut demarrer.")
    start_route(db, route)
    db.commit()
    db.refresh(route)
    return route


@router.post("/delivery-routes/{route_id}/finish", response_model=DeliveryRouteRead)
def finish_route_endpoint(
    route_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    route = db.get(DeliveryRoute, route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Tournee introuvable.")
    if route.state != "en_livraison":
        raise HTTPException(status_code=400, detail="Seule une tournee en livraison peut etre terminee.")
    if not route_can_finish(route):
        raise HTTPException(
            status_code=400, detail="Toutes les livraisons de la tournee doivent etre confirmees (ou en probleme)."
        )
    finish_route(db, route)
    db.commit()
    db.refresh(route)
    return route


@router.post("/delivery-routes/{route_id}/close", response_model=DeliveryRouteRead)
def close_route_endpoint(
    route_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    route = db.get(DeliveryRoute, route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Tournee introuvable.")
    if route.state != "livree":
        raise HTTPException(status_code=400, detail="Seule une tournee livree peut etre cloturee.")
    close_route(db, route)
    db.commit()
    db.refresh(route)
    return route


@router.get("/deliveries", response_model=list[DeliveryRead])
def list_deliveries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Delivery)
    stmt = scope_deliveries_by_driver(stmt, db, current_user)
    return db.execute(stmt).scalars().unique().all()


@router.get("/deliveries/{delivery_id}", response_model=DeliveryRead)
def read_delivery(delivery_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    delivery = db.get(Delivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Livraison introuvable.")
    return delivery


@router.post("/deliveries", response_model=DeliveryRead, status_code=status.HTTP_201_CREATED)
def create_delivery(
    payload: DeliveryCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*LOGISTICS_MANAGERS))
):
    route = db.get(DeliveryRoute, payload.route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Tournee introuvable.")
    if route.state != "planifiee":
        raise HTTPException(status_code=400, detail="Impossible d'ajouter une livraison a une tournee deja chargee.")

    order = db.get(SaleOrder, payload.sale_order_id)
    if order is None or order.state != "commande":
        raise HTTPException(
            status_code=400, detail="La livraison requiert une commande confirmee (etat 'commande')."
        )
    if db.query(Delivery).filter(Delivery.sale_order_id == payload.sale_order_id).count():
        raise HTTPException(status_code=400, detail="Cette commande a deja une livraison.")

    delivery = Delivery(route_id=route.id, sale_order_id=order.id, state="planifiee")
    delivery.reference = next_reference(db, code="delivery", prefix="LIV")
    for line in order.lines:
        delivery.lines.append(
            DeliveryLine(product_id=line.product_id, ordered_qty=line.qty, delivered_qty=0.0)
        )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


@router.post("/deliveries/{delivery_id}/confirm", response_model=DeliveryRead)
def confirm_delivery_endpoint(
    delivery_id: int,
    payload: DeliveryConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*DELIVERY_CONFIRMERS)),
):
    delivery = db.get(Delivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Livraison introuvable.")
    if is_driver_restricted(current_user):
        own_driver = db.query(Driver).filter(Driver.user_id == current_user.id).one_or_none()
        if own_driver is None or delivery.route.driver_id != own_driver.id:
            raise HTTPException(status_code=403, detail="Cette livraison ne vous est pas assignee.")
    if delivery.state not in ("chargee", "en_livraison"):
        raise HTTPException(
            status_code=400, detail="Seule une livraison chargee ou en cours peut etre confirmee."
        )
    if not payload.issue_description and not payload.signature_data:
        raise HTTPException(
            status_code=400, detail="Une signature est requise, sauf en cas de signalement de probleme."
        )

    lines_by_id = {line.id: line for line in delivery.lines}
    qty_by_line = {}
    for entry in payload.lines:
        line = lines_by_id.get(entry.line_id)
        if line is None:
            raise HTTPException(status_code=400, detail="Ligne de livraison introuvable.")
        if entry.delivered_qty < 0 or entry.delivered_qty > line.ordered_qty:
            raise HTTPException(
                status_code=400, detail="La quantite livree doit etre comprise entre 0 et la quantite commandee."
            )
        qty_by_line[entry.line_id] = entry.delivered_qty

    confirm_delivery(
        db,
        delivery,
        qty_by_line,
        signature_data=payload.signature_data,
        photo_url=payload.photo_url,
        gps_latitude=payload.gps_latitude,
        gps_longitude=payload.gps_longitude,
        issue_description=payload.issue_description,
    )
    db.commit()
    db.refresh(delivery)
    return delivery
