from tests.conftest import auth_headers, make_user


def _confirmed_order(client, headers, qty=10, unit_price=100.0):
    supplier = client.post(
        "/api/partners", json={"name": "Fournisseur IMP", "is_supplier": True}, headers=headers
    ).json()
    uom_cat = client.post("/api/uom-categories", json={"name": "Unite IMP"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": "Piece IMP", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": "Produit IMP", "uom_id": uom["id"]}, headers=headers).json()
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


def test_create_import_requires_confirmed_order(client, db):
    make_user(db, email="achats_imp1@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp1@example.com")
    supplier = client.post(
        "/api/partners", json={"name": "Fournisseur non confirme", "is_supplier": True}, headers=headers
    ).json()
    order = client.post(
        "/api/purchase-orders", json={"supplier_id": supplier["id"], "order_date": "2026-01-15"}, headers=headers
    ).json()
    resp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers)
    assert resp.status_code == 400


def test_only_one_import_per_purchase_order(client, db):
    make_user(db, email="achats_imp2@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp2@example.com")
    order, _ = _confirmed_order(client, headers)
    resp1 = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers)
    assert resp1.status_code == 201
    resp2 = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers)
    assert resp2.status_code == 400


def test_import_reference_generated(client, db):
    make_user(db, email="achats_imp3@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp3@example.com")
    order, _ = _confirmed_order(client, headers)
    resp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers)
    assert resp.json()["reference"].startswith("IMP")
    assert resp.json()["state"] == "nouveau"


def test_advance_through_full_workflow(client, db):
    make_user(db, email="achats_imp4@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp4@example.com")
    order, _ = _confirmed_order(client, headers)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()

    states = ["expedie", "arrive", "douane", "receptionne"]
    for expected_state in states:
        resp = client.post(f"/api/imports/{imp['id']}/advance", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["state"] == expected_state


def test_cannot_advance_past_receptionne(client, db):
    make_user(db, email="achats_imp5@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp5@example.com")
    order, _ = _confirmed_order(client, headers)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()
    for _ in range(4):
        client.post(f"/api/imports/{imp['id']}/advance", headers=headers)
    resp = client.post(f"/api/imports/{imp['id']}/advance", headers=headers)
    assert resp.status_code == 400


def test_real_cost_allocated_to_product_on_receptionne(client, db):
    make_user(db, email="achats_imp6@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp6@example.com")
    order, product = _confirmed_order(client, headers, qty=10, unit_price=100.0)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()

    client.patch(
        f"/api/imports/{imp['id']}",
        json={"transport_cost": 100.0, "customs_cost": 50.0, "transit_cost": 30.0, "other_costs": 20.0},
        headers=headers,
    )
    for _ in range(4):
        resp = client.post(f"/api/imports/{imp['id']}/advance", headers=headers)
    assert resp.json()["state"] == "receptionne"

    # order_subtotal = 1000, extra_costs = 200, single line -> real unit cost = (1000+200)/10 = 120
    product_resp = client.get(f"/api/products/{product['id']}", headers=headers)
    assert product_resp.json()["cost_price"] == 120.0


def test_real_cost_allocated_pro_rata_across_multiple_lines(client, db):
    make_user(db, email="achats_imp7@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp7@example.com")
    supplier = client.post(
        "/api/partners", json={"name": "Fournisseur Multi", "is_supplier": True}, headers=headers
    ).json()
    uom_cat = client.post("/api/uom-categories", json={"name": "Unite Multi"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": "Piece Multi", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product_a = client.post("/api/products", json={"name": "Produit A", "uom_id": uom["id"]}, headers=headers).json()
    product_b = client.post("/api/products", json={"name": "Produit B", "uom_id": uom["id"]}, headers=headers).json()

    order = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [
                {"product_id": product_a["id"], "qty": 10, "unit_price": 80.0},  # subtotal 800 (80%)
                {"product_id": product_b["id"], "qty": 10, "unit_price": 20.0},  # subtotal 200 (20%)
            ],
        },
        headers=headers,
    ).json()
    client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()
    client.patch(f"/api/imports/{imp['id']}", json={"transport_cost": 100.0}, headers=headers)
    for _ in range(4):
        client.post(f"/api/imports/{imp['id']}/advance", headers=headers)

    # extra_costs = 100, A gets 80% = 80 -> (800+80)/10 = 88 ; B gets 20% = 20 -> (200+20)/10 = 22
    a = client.get(f"/api/products/{product_a['id']}", headers=headers).json()
    b = client.get(f"/api/products/{product_b['id']}", headers=headers).json()
    assert a["cost_price"] == 88.0
    assert b["cost_price"] == 22.0


def test_cannot_modify_receptionne_import(client, db):
    make_user(db, email="achats_imp8@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_imp8@example.com")
    order, _ = _confirmed_order(client, headers)
    imp = client.post("/api/imports", json={"purchase_order_id": order["id"]}, headers=headers).json()
    for _ in range(4):
        client.post(f"/api/imports/{imp['id']}/advance", headers=headers)
    resp = client.patch(f"/api/imports/{imp['id']}", json={"port": "Douala"}, headers=headers)
    assert resp.status_code == 400


def test_create_container(client, db):
    make_user(db, email="achats_cont1@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_cont1@example.com")
    resp = client.post("/api/containers", json={"number": "MSCU1234567", "size": "40ft"}, headers=headers)
    assert resp.status_code == 201


def test_duplicate_container_number_rejected(client, db):
    make_user(db, email="achats_cont2@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_cont2@example.com")
    client.post("/api/containers", json={"number": "DUPL0000001"}, headers=headers)
    resp = client.post("/api/containers", json={"number": "DUPL0000001"}, headers=headers)
    assert resp.status_code == 400
