from tests.conftest import auth_headers, make_user

LOGISTICS_ROLES = ["logistique", "achats", "ventes", "stock"]


def _setup_confirmed_order(client, headers, code, qty=10, unit_price=100.0):
    customer = client.post(
        "/api/partners", json={"name": f"Client {code}", "is_customer": True}, headers=headers
    ).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {code}"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {code}", "uom_id": uom["id"]}, headers=headers).json()
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-03-01",
            "lines": [{"product_id": product["id"], "qty": qty, "unit_price": unit_price}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 200, resp.text
    return product, resp.json()


def _setup_route(client, headers, code, warehouse=True, driver_user_id=None):
    warehouse_id = None
    if warehouse:
        wh = client.post("/api/warehouses", json={"name": f"Entrepot {code}", "code": f"WH-{code}"}, headers=headers).json()
        warehouse_id = wh["id"]
    driver = client.post(
        "/api/drivers", json={"name": f"Chauffeur {code}", "user_id": driver_user_id}, headers=headers
    ).json()
    vehicle = client.post(
        "/api/vehicles", json={"name": f"Camion {code}", "plate_number": f"TCH-{code}"}, headers=headers
    ).json()
    route = client.post(
        "/api/delivery-routes",
        json={"driver_id": driver["id"], "vehicle_id": vehicle["id"], "warehouse_id": warehouse_id, "route_date": "2026-03-02"},
        headers=headers,
    ).json()
    return driver, vehicle, route


def test_full_route_and_delivery_happy_path(client, db):
    make_user(db, email="logi1@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi1@example.com")
    product, order = _setup_confirmed_order(client, headers, "D1", qty=10, unit_price=100.0)
    driver, vehicle, route = _setup_route(client, headers, "D1")
    assert route["reference"].startswith("TRN")
    assert route["state"] == "planifiee"

    delivery = client.post(
        "/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers
    ).json()
    assert delivery["reference"].startswith("LIV")
    assert delivery["state"] == "planifiee"
    assert delivery["lines"][0]["ordered_qty"] == 10

    resp = client.post(f"/api/delivery-routes/{route['id']}/load", headers=headers)
    assert resp.json()["state"] == "chargee"
    delivery = client.get(f"/api/deliveries/{delivery['id']}", headers=headers).json()
    assert delivery["state"] == "chargee"

    resp = client.post(f"/api/delivery-routes/{route['id']}/start", headers=headers)
    assert resp.json()["state"] == "en_livraison"
    delivery = client.get(f"/api/deliveries/{delivery['id']}", headers=headers).json()
    assert delivery["state"] == "en_livraison"

    line_id = delivery["lines"][0]["id"]
    resp = client.post(
        f"/api/deliveries/{delivery['id']}/confirm",
        json={"lines": [{"line_id": line_id, "delivered_qty": 10}], "signature_data": "base64-signature"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    confirmed = resp.json()
    assert confirmed["state"] == "livree"
    assert confirmed["delivered_at"] is not None

    moves = client.get(f"/api/stock-moves?product_id={product['id']}", headers=headers).json()
    out_moves = [m for m in moves if m["move_type"] == "out" and m["reason"] == f"Livraison {delivery['reference']}"]
    assert len(out_moves) == 1
    assert out_moves[0]["qty"] == 10

    resp = client.post(f"/api/delivery-routes/{route['id']}/finish", headers=headers)
    assert resp.json()["state"] == "livree"
    resp = client.post(f"/api/delivery-routes/{route['id']}/close", headers=headers)
    assert resp.json()["state"] == "cloturee"


def test_partial_delivery_creates_partial_stock_move(client, db):
    make_user(db, email="logi2@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi2@example.com")
    product, order = _setup_confirmed_order(client, headers, "D2", qty=10)
    _, _, route = _setup_route(client, headers, "D2")
    delivery = client.post(
        "/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers
    ).json()
    client.post(f"/api/delivery-routes/{route['id']}/load", headers=headers)
    client.post(f"/api/delivery-routes/{route['id']}/start", headers=headers)

    line_id = delivery["lines"][0]["id"]
    resp = client.post(
        f"/api/deliveries/{delivery['id']}/confirm",
        json={"lines": [{"line_id": line_id, "delivered_qty": 4}], "signature_data": "sig"},
        headers=headers,
    )
    assert resp.json()["state"] == "partielle"

    moves = client.get(f"/api/stock-moves?product_id={product['id']}", headers=headers).json()
    out_moves = [m for m in moves if m["move_type"] == "out" and m["reason"] == f"Livraison {delivery['reference']}"]
    assert len(out_moves) == 1
    assert out_moves[0]["qty"] == 4


def test_issue_report_without_signature_and_no_stock_move(client, db):
    make_user(db, email="logi3@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi3@example.com")
    product, order = _setup_confirmed_order(client, headers, "D3", qty=5)
    _, _, route = _setup_route(client, headers, "D3")
    delivery = client.post(
        "/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers
    ).json()
    client.post(f"/api/delivery-routes/{route['id']}/load", headers=headers)
    client.post(f"/api/delivery-routes/{route['id']}/start", headers=headers)

    line_id = delivery["lines"][0]["id"]
    resp = client.post(
        f"/api/deliveries/{delivery['id']}/confirm",
        json={"lines": [{"line_id": line_id, "delivered_qty": 0}], "issue_description": "Client absent"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["state"] == "probleme"

    moves = client.get(f"/api/stock-moves?product_id={product['id']}", headers=headers).json()
    out_moves = [m for m in moves if m["move_type"] == "out" and m["reason"] == f"Livraison {delivery['reference']}"]
    assert len(out_moves) == 0


def test_confirm_requires_signature_or_issue(client, db):
    make_user(db, email="logi4@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi4@example.com")
    _, order = _setup_confirmed_order(client, headers, "D4", qty=3)
    _, _, route = _setup_route(client, headers, "D4")
    delivery = client.post(
        "/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers
    ).json()
    client.post(f"/api/delivery-routes/{route['id']}/load", headers=headers)
    client.post(f"/api/delivery-routes/{route['id']}/start", headers=headers)

    line_id = delivery["lines"][0]["id"]
    resp = client.post(
        f"/api/deliveries/{delivery['id']}/confirm",
        json={"lines": [{"line_id": line_id, "delivered_qty": 3}]},
        headers=headers,
    )
    assert resp.status_code == 400


def test_delivered_qty_cannot_exceed_ordered_qty(client, db):
    make_user(db, email="logi5@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi5@example.com")
    _, order = _setup_confirmed_order(client, headers, "D5", qty=3)
    _, _, route = _setup_route(client, headers, "D5")
    delivery = client.post(
        "/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers
    ).json()
    client.post(f"/api/delivery-routes/{route['id']}/load", headers=headers)
    client.post(f"/api/delivery-routes/{route['id']}/start", headers=headers)

    line_id = delivery["lines"][0]["id"]
    resp = client.post(
        f"/api/deliveries/{delivery['id']}/confirm",
        json={"lines": [{"line_id": line_id, "delivered_qty": 999}], "signature_data": "sig"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_cannot_create_delivery_for_unconfirmed_order(client, db):
    make_user(db, email="logi6@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi6@example.com")
    customer = client.post("/api/partners", json={"name": "Client D6", "is_customer": True}, headers=headers).json()
    order = client.post(
        "/api/sale-orders", json={"customer_id": customer["id"], "order_date": "2026-03-01"}, headers=headers
    ).json()
    _, _, route = _setup_route(client, headers, "D6")
    resp = client.post(
        "/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers
    )
    assert resp.status_code == 400


def test_cannot_create_two_deliveries_for_same_order(client, db):
    make_user(db, email="logi7@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi7@example.com")
    _, order = _setup_confirmed_order(client, headers, "D7", qty=2)
    _, _, route = _setup_route(client, headers, "D7")
    resp1 = client.post("/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers)
    assert resp1.status_code == 201
    resp2 = client.post("/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers)
    assert resp2.status_code == 400


def test_route_cannot_finish_before_all_deliveries_terminal(client, db):
    make_user(db, email="logi8@example.com", role_codes=LOGISTICS_ROLES)
    headers = auth_headers(client, "logi8@example.com")
    _, order = _setup_confirmed_order(client, headers, "D8", qty=2)
    _, _, route = _setup_route(client, headers, "D8")
    client.post("/api/deliveries", json={"route_id": route["id"], "sale_order_id": order["id"]}, headers=headers)
    client.post(f"/api/delivery-routes/{route['id']}/load", headers=headers)
    client.post(f"/api/delivery-routes/{route['id']}/start", headers=headers)
    resp = client.post(f"/api/delivery-routes/{route['id']}/finish", headers=headers)
    assert resp.status_code == 400


def test_stock_role_cannot_manage_fleet_or_routes(client, db):
    make_user(db, email="stock_d1@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock_d1@example.com")
    resp = client.post("/api/vehicles", json={"name": "Camion X", "plate_number": "TCH-X1"}, headers=headers)
    assert resp.status_code == 403
    resp = client.post("/api/drivers", json={"name": "Chauffeur X"}, headers=headers)
    assert resp.status_code == 403
    resp = client.post(
        "/api/delivery-routes",
        json={"driver_id": 1, "vehicle_id": 1, "route_date": "2026-03-02"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_driver_sees_only_own_routes_and_deliveries(client, db):
    make_user(db, email="logi9@example.com", role_codes=LOGISTICS_ROLES)
    logi_headers = auth_headers(client, "logi9@example.com")

    driver_user_a = make_user(db, email="chauffeur_a@example.com", role_codes=["chauffeur"])
    driver_user_b = make_user(db, email="chauffeur_b@example.com", role_codes=["chauffeur"])

    product, order_a = _setup_confirmed_order(client, logi_headers, "D9A", qty=4)
    _, order_b = _setup_confirmed_order(client, logi_headers, "D9B", qty=6)

    driver_a, _, route_a = _setup_route(client, logi_headers, "D9A", driver_user_id=driver_user_a.id)
    driver_b, _, route_b = _setup_route(client, logi_headers, "D9B", driver_user_id=driver_user_b.id)

    delivery_a = client.post(
        "/api/deliveries", json={"route_id": route_a["id"], "sale_order_id": order_a["id"]}, headers=logi_headers
    ).json()
    delivery_b = client.post(
        "/api/deliveries", json={"route_id": route_b["id"], "sale_order_id": order_b["id"]}, headers=logi_headers
    ).json()

    headers_a = auth_headers(client, "chauffeur_a@example.com")

    routes_seen = client.get("/api/delivery-routes", headers=headers_a).json()
    assert {r["id"] for r in routes_seen} == {route_a["id"]}

    deliveries_seen = client.get("/api/deliveries", headers=headers_a).json()
    assert {d["id"] for d in deliveries_seen} == {delivery_a["id"]}

    client.post(f"/api/delivery-routes/{route_b['id']}/load", headers=logi_headers)
    client.post(f"/api/delivery-routes/{route_b['id']}/start", headers=logi_headers)
    resp = client.post(
        f"/api/deliveries/{delivery_b['id']}/confirm",
        json={"lines": [{"line_id": delivery_b["lines"][0]["id"], "delivered_qty": 6}], "signature_data": "sig"},
        headers=headers_a,
    )
    assert resp.status_code == 403


def test_chauffeur_without_linked_driver_sees_nothing(client, db):
    make_user(db, email="logi10@example.com", role_codes=LOGISTICS_ROLES)
    logi_headers = auth_headers(client, "logi10@example.com")
    make_user(db, email="chauffeur_orphan@example.com", role_codes=["chauffeur"])
    _setup_route(client, logi_headers, "D10")
    headers_orphan = auth_headers(client, "chauffeur_orphan@example.com")
    routes_seen = client.get("/api/delivery-routes", headers=headers_orphan).json()
    assert routes_seen == []
