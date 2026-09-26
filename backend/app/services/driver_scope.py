"""Row-level scoping for the chauffeur role, mirroring app.services.rbac's
branch scoping: a user holding ONLY the chauffeur role (not logistique,
not direction_generale, not superuser) sees only routes/deliveries
assigned to the driver record linked to their own account - "Mes
livraisons" - and sees nothing at all if no driver record is linked
(secure-by-default).
"""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.delivery import Delivery, DeliveryRoute
from app.models.fleet import Driver
from app.models.user import User

RESTRICTED_ROLE = "chauffeur"
UNRESTRICTED_ROLES = {"logistique", "direction_generale"}


def is_driver_restricted(user: User) -> bool:
    if user.is_superuser:
        return False
    role_codes = {r.code for r in user.roles}
    return RESTRICTED_ROLE in role_codes and not (role_codes & UNRESTRICTED_ROLES)


def _own_driver_id(db: Session, user: User) -> int | None:
    driver = db.execute(select(Driver).where(Driver.user_id == user.id)).scalar_one_or_none()
    return driver.id if driver else None


def scope_routes_by_driver(stmt: Select, db: Session, user: User) -> Select:
    if not is_driver_restricted(user):
        return stmt
    driver_id = _own_driver_id(db, user)
    if driver_id is None:
        return stmt.where(DeliveryRoute.id.in_([]))
    return stmt.where(DeliveryRoute.driver_id == driver_id)


def scope_deliveries_by_driver(stmt: Select, db: Session, user: User) -> Select:
    if not is_driver_restricted(user):
        return stmt
    driver_id = _own_driver_id(db, user)
    if driver_id is None:
        return stmt.where(Delivery.id.in_([]))
    return stmt.join(DeliveryRoute, Delivery.route_id == DeliveryRoute.id).where(
        DeliveryRoute.driver_id == driver_id
    )
