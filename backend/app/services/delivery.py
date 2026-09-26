"""Business logic for delivery routes and deliveries: cascading a route's
loading/departure into its deliveries' own state, and confirming a
delivery (proof of delivery + the resulting real stock-out move). Kept
out of the router so the "route state drives delivery state" rule - the
bug that had to be fixed after the fact in the earlier version of this
project - is enforced in exactly one place from the start.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.delivery import DELIVERY_TERMINAL_STATES, Delivery, DeliveryRoute
from app.models.stock import StockMove


def load_route(db: Session, route: DeliveryRoute) -> None:
    for delivery in route.deliveries:
        if delivery.state == "planifiee":
            delivery.state = "chargee"
    route.state = "chargee"


def start_route(db: Session, route: DeliveryRoute) -> None:
    for delivery in route.deliveries:
        if delivery.state == "chargee":
            delivery.state = "en_livraison"
    route.state = "en_livraison"


def finish_route(db: Session, route: DeliveryRoute) -> None:
    route.state = "livree"


def close_route(db: Session, route: DeliveryRoute) -> None:
    route.state = "cloturee"


def confirm_delivery(
    db: Session,
    delivery: Delivery,
    delivered_qty_by_line_id: dict[int, float],
    signature_data: str | None,
    photo_url: str | None,
    gps_latitude: float | None,
    gps_longitude: float | None,
    issue_description: str | None,
) -> Delivery:
    for line in delivery.lines:
        if line.id in delivered_qty_by_line_id:
            line.delivered_qty = delivered_qty_by_line_id[line.id]

    total_ordered = sum(line.ordered_qty for line in delivery.lines)
    total_delivered = sum(line.delivered_qty for line in delivery.lines)

    if issue_description:
        delivery.state = "probleme"
    elif total_delivered >= total_ordered:
        delivery.state = "livree"
    elif total_delivered > 0:
        delivery.state = "partielle"
    else:
        delivery.state = "probleme"

    delivery.signature_data = signature_data
    delivery.photo_url = photo_url
    delivery.gps_latitude = gps_latitude
    delivery.gps_longitude = gps_longitude
    delivery.issue_description = issue_description
    delivery.delivered_at = datetime.now(timezone.utc)

    warehouse_id = delivery.route.warehouse_id
    if warehouse_id is not None:
        for line in delivery.lines:
            if line.delivered_qty > 0:
                db.add(
                    StockMove(
                        move_type="out",
                        product_id=line.product_id,
                        qty=line.delivered_qty,
                        source_warehouse_id=warehouse_id,
                        state="done",
                        reason=f"Livraison {delivery.reference}",
                    )
                )
    db.flush()
    return delivery


def route_can_finish(route: DeliveryRoute) -> bool:
    return bool(route.deliveries) and all(d.state in DELIVERY_TERMINAL_STATES for d in route.deliveries)
