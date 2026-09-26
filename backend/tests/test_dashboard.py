from tests.conftest import auth_headers, make_user

DASHBOARD_ROLES = ["direction_generale", "achats", "ventes", "stock", "logistique", "comptable", "caissier", "rh"]


def test_dashboard_requires_direction_generale(client, db):
    make_user(db, email="dash1@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "dash1@example.com")
    resp = client.get("/api/dashboard/summary?period_start=2026-01-01&period_end=2026-12-31", headers=headers)
    assert resp.status_code == 403


def test_dashboard_low_stock_alert(client, db):
    make_user(db, email="dash2@example.com", role_codes=DASHBOARD_ROLES)
    headers = auth_headers(client, "dash2@example.com")
    uom_cat = client.post("/api/uom-categories", json={"name": "Unite Dash2"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": "Piece Dash2", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post(
        "/api/products",
        json={"name": "Produit Dash2", "uom_id": uom["id"], "min_stock_qty": 100},
        headers=headers,
    ).json()

    resp = client.get("/api/dashboard/summary?period_start=2026-01-01&period_end=2026-12-31", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    alert = next((a for a in body["stock"]["low_stock_products"] if a["product_id"] == product["id"]), None)
    assert alert is not None
    assert alert["qty_on_hand"] == 0.0
    assert alert["min_stock_qty"] == 100.0


def test_dashboard_reflects_cash_and_bank_and_receivables(client, db):
    make_user(db, email="dash3@example.com", role_codes=DASHBOARD_ROLES)
    headers = auth_headers(client, "dash3@example.com")

    register = client.post("/api/cash-registers", json={"name": "Caisse Dash3", "code": "CR-DASH3"}, headers=headers).json()
    session = client.post(
        "/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 700}, headers=headers
    ).json()
    account = client.post(
        "/api/bank-accounts",
        json={"name": "Compte Dash3", "bank_name": "Banque Tchad", "account_number": "ACC-DASH3", "opening_balance": 1200},
        headers=headers,
    ).json()

    customer = client.post("/api/partners", json={"name": "Client Dash3", "is_customer": True}, headers=headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": "Unite Dash3"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": "Piece Dash3", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": "Produit Dash3", "uom_id": uom["id"]}, headers=headers).json()
    order = client.post(
        "/api/sale-orders",
        json={"customer_id": customer["id"], "order_date": "2026-06-01", "lines": [{"product_id": product["id"], "qty": 2, "unit_price": 300}]},
        headers=headers,
    ).json()
    client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=headers).json()
    client.post(f"/api/invoices/{invoice['id']}/validate", headers=headers)

    resp = client.get("/api/dashboard/summary?period_start=2026-01-01&period_end=2026-12-31", headers=headers)
    body = resp.json()

    cash_entry = next(c for c in body["finance"]["cash_sessions"] if c["session_id"] == session["id"])
    assert cash_entry["balance"] == 700.0

    bank_entry = next(b for b in body["finance"]["bank_accounts"] if b["account_id"] == account["id"])
    assert bank_entry["balance"] == 1200.0

    assert body["finance"]["total_receivables"] >= 600.0
    assert body["sales"]["total_confirmed_sales"] >= 600.0


def test_dashboard_includes_pending_leave_and_open_routes(client, db):
    make_user(db, email="dash4@example.com", role_codes=DASHBOARD_ROLES)
    headers = auth_headers(client, "dash4@example.com")
    employee = client.post(
        "/api/employees",
        json={"name": "Employe Dash4", "position": "Vendeur", "hire_date": "2026-01-01", "base_salary": 1000},
        headers=headers,
    ).json()
    client.post(
        "/api/leave-requests",
        json={"employee_id": employee["id"], "start_date": "2026-07-01", "end_date": "2026-07-03"},
        headers=headers,
    )

    driver = client.post("/api/drivers", json={"name": "Chauffeur Dash4"}, headers=headers).json()
    vehicle = client.post("/api/vehicles", json={"name": "Camion Dash4", "plate_number": "TCH-DASH4"}, headers=headers).json()
    client.post(
        "/api/delivery-routes",
        json={"driver_id": driver["id"], "vehicle_id": vehicle["id"], "route_date": "2026-07-05"},
        headers=headers,
    )

    resp = client.get("/api/dashboard/summary?period_start=2026-01-01&period_end=2026-12-31", headers=headers)
    body = resp.json()
    assert body["hr"]["pending_leave_requests"] >= 1
    assert body["distribution"]["open_delivery_routes"] >= 1
