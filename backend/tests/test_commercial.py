from tests.conftest import auth_headers, make_user

SALES_ROLES = ["ventes", "achats", "direction_generale"]


def _setup_customer_and_product(client, headers, code):
    customer = client.post("/api/partners", json={"name": f"Client {code}", "is_customer": True}, headers=headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {code}"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {code}", "uom_id": uom["id"]}, headers=headers).json()
    return customer, product


def _confirmed_order(client, headers, customer, product, sales_rep_id, order_date, qty, unit_price):
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "sales_rep_id": sales_rep_id,
            "order_date": order_date,
            "lines": [{"product_id": product["id"], "qty": qty, "unit_price": unit_price}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_sales_rep_requires_direction_generale(client, db):
    make_user(db, email="com1@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "com1@example.com")
    resp = client.post("/api/sales-reps", json={"name": "Commercial X", "commission_rate": 5}, headers=headers)
    assert resp.status_code == 403


def test_commission_computed_live_from_confirmed_orders(client, db):
    make_user(db, email="com2@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com2@example.com")
    rep = client.post("/api/sales-reps", json={"name": "Commercial C2", "commission_rate": 10}, headers=headers).json()
    customer, product = _setup_customer_and_product(client, headers, "C2")

    _confirmed_order(client, headers, customer, product, rep["id"], "2026-06-01", qty=10, unit_price=100.0)  # 1000
    _confirmed_order(client, headers, customer, product, rep["id"], "2026-06-15", qty=5, unit_price=200.0)  # 1000

    resp = client.get(
        f"/api/sales-reps/{rep['id']}/commission?period_start=2026-06-01&period_end=2026-06-30", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["commission"] == 200.0  # 10% of 2000


def test_commission_excludes_orders_outside_period(client, db):
    make_user(db, email="com3@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com3@example.com")
    rep = client.post("/api/sales-reps", json={"name": "Commercial C3", "commission_rate": 20}, headers=headers).json()
    customer, product = _setup_customer_and_product(client, headers, "C3")

    _confirmed_order(client, headers, customer, product, rep["id"], "2026-05-31", qty=1, unit_price=1000.0)
    _confirmed_order(client, headers, customer, product, rep["id"], "2026-06-15", qty=1, unit_price=500.0)

    resp = client.get(
        f"/api/sales-reps/{rep['id']}/commission?period_start=2026-06-01&period_end=2026-06-30", headers=headers
    )
    assert resp.json()["commission"] == 100.0  # 20% of 500 only


def test_commission_excludes_devis_and_cancelled_orders(client, db):
    make_user(db, email="com4@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com4@example.com")
    rep = client.post("/api/sales-reps", json={"name": "Commercial C4", "commission_rate": 10}, headers=headers).json()
    customer, product = _setup_customer_and_product(client, headers, "C4")

    devis = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "sales_rep_id": rep["id"],
            "order_date": "2026-06-05",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 5000.0}],
        },
        headers=headers,
    ).json()
    # left in devis state - never confirmed

    cancelled_order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "sales_rep_id": rep["id"],
            "order_date": "2026-06-06",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 3000.0}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/sale-orders/{cancelled_order['id']}/cancel", headers=headers)

    resp = client.get(
        f"/api/sales-reps/{rep['id']}/commission?period_start=2026-06-01&period_end=2026-06-30", headers=headers
    )
    assert resp.json()["commission"] == 0.0
    assert devis["state"] == "devis"


def test_sales_target_achievement_percent(client, db):
    make_user(db, email="com5@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com5@example.com")
    rep = client.post("/api/sales-reps", json={"name": "Commercial C5", "commission_rate": 0}, headers=headers).json()
    customer, product = _setup_customer_and_product(client, headers, "C5")

    _confirmed_order(client, headers, customer, product, rep["id"], "2026-07-10", qty=1, unit_price=750.0)

    target = client.post(
        "/api/sales-targets",
        json={"sales_rep_id": rep["id"], "period_start": "2026-07-01", "period_end": "2026-07-31", "target_amount": 1500.0},
        headers=headers,
    ).json()
    assert target["achieved_amount"] == 750.0
    assert target["achievement_percent"] == 50.0


def test_sales_target_period_end_before_start_rejected(client, db):
    make_user(db, email="com6@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com6@example.com")
    rep = client.post("/api/sales-reps", json={"name": "Commercial C6", "commission_rate": 0}, headers=headers).json()
    resp = client.post(
        "/api/sales-targets",
        json={"sales_rep_id": rep["id"], "period_start": "2026-07-31", "period_end": "2026-07-01", "target_amount": 100.0},
        headers=headers,
    )
    assert resp.status_code == 422


def test_commission_rate_out_of_range_rejected(client, db):
    make_user(db, email="com7@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com7@example.com")
    resp = client.post("/api/sales-reps", json={"name": "Commercial C7", "commission_rate": 150}, headers=headers)
    assert resp.status_code == 422


def test_sale_order_without_sales_rep_still_works(client, db):
    make_user(db, email="com8@example.com", role_codes=SALES_ROLES)
    headers = auth_headers(client, "com8@example.com")
    customer, product = _setup_customer_and_product(client, headers, "C8")
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-06-01",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 100.0}],
        },
        headers=headers,
    )
    assert order.status_code == 201
    assert order.json()["sales_rep_id"] is None
