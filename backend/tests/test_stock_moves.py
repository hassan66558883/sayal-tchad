from tests.conftest import auth_headers, make_user


def _setup_warehouse_and_product(client, headers, wh_code="WH1"):
    warehouse = client.post("/api/warehouses", json={"name": f"Entrepot {wh_code}", "code": wh_code}, headers=headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {wh_code}"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {wh_code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {wh_code}", "uom_id": uom["id"]}, headers=headers).json()
    return warehouse, product


def test_create_warehouse(client, db):
    make_user(db, email="stock1@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock1@example.com")
    resp = client.post("/api/warehouses", json={"name": "Entrepot Principal", "code": "WHPRIN"}, headers=headers)
    assert resp.status_code == 201


def test_ventes_cannot_create_warehouse(client, db):
    make_user(db, email="ventes_wh@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_wh@example.com")
    resp = client.post("/api/warehouses", json={"name": "X", "code": "WHX"}, headers=headers)
    assert resp.status_code == 403


def test_in_move_requires_dest_warehouse(client, db):
    make_user(db, email="stock2@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock2@example.com")
    _, product = _setup_warehouse_and_product(client, headers, "WH2")
    resp = client.post(
        "/api/stock-moves", json={"move_type": "in", "product_id": product["id"], "qty": 10}, headers=headers
    )
    assert resp.status_code == 400


def test_in_move_then_validate_increases_qty_on_hand(client, db):
    make_user(db, email="stock3@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock3@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "WH3")

    move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 100, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    assert move["state"] == "draft"

    # Draft moves don't count yet
    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_on_hand"] == 0

    client.post(f"/api/stock-moves/{move['id']}/validate", headers=headers)
    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_on_hand"] == 100


def test_out_move_decreases_qty_on_hand(client, db):
    make_user(db, email="stock4@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock4@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "WH4")

    in_move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 50, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{in_move['id']}/validate", headers=headers)

    out_move = client.post(
        "/api/stock-moves",
        json={"move_type": "out", "product_id": product["id"], "qty": 20, "source_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{out_move['id']}/validate", headers=headers)

    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_on_hand"] == 30


def test_transfer_moves_qty_between_warehouses(client, db):
    make_user(db, email="stock5@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock5@example.com")
    wh_a, product = _setup_warehouse_and_product(client, headers, "WH5A")
    wh_b = client.post("/api/warehouses", json={"name": "Entrepot WH5B", "code": "WH5B"}, headers=headers).json()

    in_move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 40, "dest_warehouse_id": wh_a["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{in_move['id']}/validate", headers=headers)

    transfer = client.post(
        "/api/stock-moves",
        json={
            "move_type": "transfer",
            "product_id": product["id"],
            "qty": 15,
            "source_warehouse_id": wh_a["id"],
            "dest_warehouse_id": wh_b["id"],
        },
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{transfer['id']}/validate", headers=headers)

    stock_a = client.get(f"/api/products/{product['id']}/stock", params={"warehouse_id": wh_a["id"]}, headers=headers).json()
    stock_b = client.get(f"/api/products/{product['id']}/stock", params={"warehouse_id": wh_b["id"]}, headers=headers).json()
    assert stock_a["qty_on_hand"] == 25
    assert stock_b["qty_on_hand"] == 15


def test_done_move_is_immutable_except_reason(client, db):
    make_user(db, email="stock6@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock6@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "WH6")
    move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 10, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{move['id']}/validate", headers=headers)

    resp = client.patch(f"/api/stock-moves/{move['id']}", json={"qty": 999}, headers=headers)
    assert resp.status_code == 400

    resp = client.patch(f"/api/stock-moves/{move['id']}", json={"reason": "Correction notee"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["reason"] == "Correction notee"


def test_cannot_validate_move_twice(client, db):
    make_user(db, email="stock7@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock7@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "WH7")
    move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 10, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{move['id']}/validate", headers=headers)
    resp = client.post(f"/api/stock-moves/{move['id']}/validate", headers=headers)
    assert resp.status_code == 400


def test_negative_qty_rejected(client, db):
    make_user(db, email="stock8@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock8@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "WH8")
    resp = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": -5, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_stock_lot(client, db):
    make_user(db, email="stock9@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock9@example.com")
    _, product = _setup_warehouse_and_product(client, headers, "WH9")
    resp = client.post(
        "/api/stock-lots", json={"product_id": product["id"], "lot_number": "LOT-001"}, headers=headers
    )
    assert resp.status_code == 201
