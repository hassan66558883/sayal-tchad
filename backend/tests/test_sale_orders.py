from tests.conftest import auth_headers, make_user


def _setup_customer_and_product(client, headers, code="SO", credit_limit=0.0):
    customer = client.post(
        "/api/partners",
        json={"name": f"Client {code}", "is_customer": True, "credit_limit": credit_limit},
        headers=headers,
    ).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {code}"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {code}", "uom_id": uom["id"]}, headers=headers).json()
    return customer, product


def test_create_sale_order_with_discount_line(client, db):
    make_user(db, email="ventes_so1@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so1@example.com")
    customer, product = _setup_customer_and_product(client, headers, "SO1")

    resp = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 10, "unit_price": 100.0, "discount_percent": 10}],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("CMD")
    assert body["amount_total"] == 900.0  # 10 * 100 * 0.9


def test_cannot_confirm_without_lines(client, db):
    make_user(db, email="ventes_so2@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so2@example.com")
    customer, _ = _setup_customer_and_product(client, headers, "SO2")
    order = client.post(
        "/api/sale-orders", json={"customer_id": customer["id"], "order_date": "2026-02-01"}, headers=headers
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 400


def test_confirm_then_terminate_workflow(client, db):
    make_user(db, email="ventes_so3@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so3@example.com")
    customer, product = _setup_customer_and_product(client, headers, "SO3")
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 5, "unit_price": 50.0}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.json()["state"] == "commande"
    resp = client.post(f"/api/sale-orders/{order['id']}/terminate", headers=headers)
    assert resp.json()["state"] == "terminee"


def test_credit_limit_blocks_confirm_when_exceeded(client, db):
    make_user(db, email="ventes_so4@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so4@example.com")
    customer, product = _setup_customer_and_product(client, headers, "SO4", credit_limit=500.0)
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 10, "unit_price": 100.0}],  # 1000 > 500
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 400


def test_credit_limit_allows_confirm_when_within_limit(client, db):
    make_user(db, email="ventes_so5@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so5@example.com")
    customer, product = _setup_customer_and_product(client, headers, "SO5", credit_limit=2000.0)
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 10, "unit_price": 100.0}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 200


def test_zero_credit_limit_means_unlimited(client, db):
    make_user(db, email="ventes_so6@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so6@example.com")
    customer, product = _setup_customer_and_product(client, headers, "SO6", credit_limit=0.0)
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 1000, "unit_price": 1000.0}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 200


def test_discount_percent_out_of_range_rejected(client, db):
    make_user(db, email="ventes_so7@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_so7@example.com")
    customer, product = _setup_customer_and_product(client, headers, "SO7")
    resp = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 10, "discount_percent": 150}],
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_stock_role_cannot_create_sale_order(client, db):
    make_user(db, email="stock_so1@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock_so1@example.com")
    resp = client.post(
        "/api/sale-orders", json={"customer_id": 1, "order_date": "2026-02-01"}, headers=headers
    )
    assert resp.status_code == 403
