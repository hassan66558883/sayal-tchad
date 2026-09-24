from tests.conftest import auth_headers, make_user


def _confirmed_order_and_import(client, headers, code="REC", qty=20, unit_price=50.0):
    supplier = client.post("/api/partners", json={"name": f"Fournisseur {code}", "is_supplier": True}, headers=headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {code}"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {code}", "uom_id": uom["id"]}, headers=headers).json()
    order = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [{"product_id": product["id"], "qty": qty, "unit_price": unit_price}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    return order, product


def test_qty_in_transit_reflects_confirmed_unreceived_order(client, db):
    make_user(db, email="rec1@example.com", role_codes=["achats"])
    headers = auth_headers(client, "rec1@example.com")
    order, product = _confirmed_order_and_import(client, headers, "REC1", qty=30)

    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_in_transit"] == 30
    assert stock["qty_on_hand"] == 0


def test_qty_in_transit_drops_to_zero_once_receptionne(client, db):
    make_user(db, email="rec2@example.com", role_codes=["achats"])
    headers = auth_headers(client, "rec2@example.com")
    order, product = _confirmed_order_and_import(client, headers, "REC2", qty=15)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()
    for _ in range(4):
        client.post(f"/api/imports/{imp['id']}/advance", headers=headers)

    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_in_transit"] == 0


def test_create_reception_generates_draft_moves_matching_order_lines(client, db):
    make_user(db, email="rec3@example.com", role_codes=["achats"])
    achats_headers = auth_headers(client, "rec3@example.com")
    order, product = _confirmed_order_and_import(client, achats_headers, "REC3", qty=40)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=achats_headers).json()
    for _ in range(4):
        client.post(f"/api/imports/{imp['id']}/advance", headers=achats_headers)

    make_user(db, email="stock_rec3@example.com", role_codes=["stock"])
    stock_headers = auth_headers(client, "stock_rec3@example.com")
    warehouse = client.post("/api/warehouses", json={"name": "Entrepot REC3", "code": "WHREC3"}, headers=stock_headers).json()

    resp = client.post(
        f"/api/imports/{imp['id']}/create-reception",
        params={"warehouse_id": warehouse["id"]},
        headers=stock_headers,
    )
    assert resp.status_code == 200, resp.text
    moves = resp.json()
    assert len(moves) == 1
    assert moves[0]["move_type"] == "in"
    assert moves[0]["qty"] == 40
    assert moves[0]["state"] == "draft"

    # Draft, so stock not yet on hand until validated
    stock = client.get(f"/api/products/{product['id']}/stock", headers=achats_headers).json()
    assert stock["qty_on_hand"] == 0

    client.post(f"/api/stock-moves/{moves[0]['id']}/validate", headers=stock_headers)
    stock = client.get(f"/api/products/{product['id']}/stock", headers=achats_headers).json()
    assert stock["qty_on_hand"] == 40


def test_cannot_create_reception_before_receptionne(client, db):
    make_user(db, email="rec4@example.com", role_codes=["achats"])
    achats_headers = auth_headers(client, "rec4@example.com")
    order, _ = _confirmed_order_and_import(client, achats_headers, "REC4")
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=achats_headers).json()

    make_user(db, email="stock_rec4@example.com", role_codes=["stock"])
    stock_headers = auth_headers(client, "stock_rec4@example.com")
    warehouse = client.post("/api/warehouses", json={"name": "Entrepot REC4", "code": "WHREC4"}, headers=stock_headers).json()

    resp = client.post(
        f"/api/imports/{imp['id']}/create-reception",
        params={"warehouse_id": warehouse["id"]},
        headers=stock_headers,
    )
    assert resp.status_code == 400


def test_achats_role_cannot_create_reception(client, db):
    make_user(db, email="rec5@example.com", role_codes=["achats"])
    headers = auth_headers(client, "rec5@example.com")
    order, _ = _confirmed_order_and_import(client, headers, "REC5")
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()
    for _ in range(4):
        client.post(f"/api/imports/{imp['id']}/advance", headers=headers)

    resp = client.post(f"/api/imports/{imp['id']}/create-reception", params={"warehouse_id": 1}, headers=headers)
    assert resp.status_code == 403
