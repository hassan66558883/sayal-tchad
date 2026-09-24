from tests.conftest import auth_headers, make_user


def _setup_warehouse_and_product(client, headers, code="INVWH"):
    warehouse = client.post("/api/warehouses", json={"name": f"Entrepot {code}", "code": code}, headers=headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {code}"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {code}", "uom_id": uom["id"]}, headers=headers).json()
    return warehouse, product


def test_inventory_validate_creates_adjustment_in_for_surplus(client, db):
    make_user(db, email="inv1@example.com", role_codes=["stock"])
    headers = auth_headers(client, "inv1@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "INV1")
    # theoretical qty is 0 (no moves yet), count 25 -> surplus of 25
    inventory = client.post(
        "/api/stock-inventories",
        json={
            "warehouse_id": warehouse["id"],
            "inventory_date": "2026-01-20",
            "lines": [{"product_id": product["id"], "counted_qty": 25}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/stock-inventories/{inventory['id']}/validate", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "validated"
    assert body["lines"][0]["theoretical_qty"] == 0

    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_on_hand"] == 25


def test_inventory_validate_creates_adjustment_out_for_shortage(client, db):
    make_user(db, email="inv2@example.com", role_codes=["stock"])
    headers = auth_headers(client, "inv2@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "INV2")

    in_move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 100, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{in_move['id']}/validate", headers=headers)

    inventory = client.post(
        "/api/stock-inventories",
        json={
            "warehouse_id": warehouse["id"],
            "inventory_date": "2026-01-20",
            "lines": [{"product_id": product["id"], "counted_qty": 90}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/stock-inventories/{inventory['id']}/validate", headers=headers)

    stock = client.get(f"/api/products/{product['id']}/stock", headers=headers).json()
    assert stock["qty_on_hand"] == 90


def test_inventory_validate_no_move_when_no_discrepancy(client, db):
    make_user(db, email="inv3@example.com", role_codes=["stock"])
    headers = auth_headers(client, "inv3@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "INV3")

    in_move = client.post(
        "/api/stock-moves",
        json={"move_type": "in", "product_id": product["id"], "qty": 50, "dest_warehouse_id": warehouse["id"]},
        headers=headers,
    ).json()
    client.post(f"/api/stock-moves/{in_move['id']}/validate", headers=headers)

    inventory = client.post(
        "/api/stock-inventories",
        json={
            "warehouse_id": warehouse["id"],
            "inventory_date": "2026-01-20",
            "lines": [{"product_id": product["id"], "counted_qty": 50}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/stock-inventories/{inventory['id']}/validate", headers=headers)

    moves = client.get("/api/stock-moves", params={"product_id": product["id"]}, headers=headers).json()
    assert len(moves) == 1  # only the original "in" move, no adjustment


def test_cannot_validate_inventory_twice(client, db):
    make_user(db, email="inv4@example.com", role_codes=["stock"])
    headers = auth_headers(client, "inv4@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "INV4")
    inventory = client.post(
        "/api/stock-inventories",
        json={
            "warehouse_id": warehouse["id"],
            "inventory_date": "2026-01-20",
            "lines": [{"product_id": product["id"], "counted_qty": 5}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/stock-inventories/{inventory['id']}/validate", headers=headers)
    resp = client.post(f"/api/stock-inventories/{inventory['id']}/validate", headers=headers)
    assert resp.status_code == 400


def test_cannot_add_line_after_validation(client, db):
    make_user(db, email="inv5@example.com", role_codes=["stock"])
    headers = auth_headers(client, "inv5@example.com")
    warehouse, product = _setup_warehouse_and_product(client, headers, "INV5")
    inventory = client.post(
        "/api/stock-inventories",
        json={"warehouse_id": warehouse["id"], "inventory_date": "2026-01-20", "lines": []},
        headers=headers,
    ).json()
    client.post(f"/api/stock-inventories/{inventory['id']}/validate", headers=headers)
    resp = client.post(
        f"/api/stock-inventories/{inventory['id']}/lines",
        json={"product_id": product["id"], "counted_qty": 1},
        headers=headers,
    )
    assert resp.status_code == 400
