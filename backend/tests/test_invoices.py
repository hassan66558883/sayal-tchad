from tests.conftest import auth_headers, make_user


def _confirmed_order(client, headers, code="INV", qty=10, unit_price=100.0):
    customer = client.post("/api/partners", json={"name": f"Client {code}", "is_customer": True}, headers=headers).json()
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
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": qty, "unit_price": unit_price}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/sale-orders/{order['id']}/confirm", headers=headers)
    return order, customer, product


def test_create_invoice_from_confirmed_order(client, db):
    make_user(db, email="ventes_inv1@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_inv1@example.com")
    order, _, _ = _confirmed_order(client, headers, "INV1")
    resp = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("FAC")
    assert body["state"] == "draft"
    assert body["amount_total"] == 1000.0
    assert body["payment_state"] == "not_paid"


def test_cannot_invoice_unconfirmed_order(client, db):
    make_user(db, email="ventes_inv2@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_inv2@example.com")
    customer = client.post("/api/partners", json={"name": "Client Devis", "is_customer": True}, headers=headers).json()
    order = client.post(
        "/api/sale-orders", json={"customer_id": customer["id"], "order_date": "2026-02-01"}, headers=headers
    ).json()
    resp = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=headers)
    assert resp.status_code == 400


def test_validate_invoice(client, db):
    make_user(db, email="ventes_inv3@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_inv3@example.com")
    order, _, _ = _confirmed_order(client, headers, "INV3")
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=headers).json()
    resp = client.post(f"/api/invoices/{invoice['id']}/validate", headers=headers)
    assert resp.json()["state"] == "validated"


def test_credit_note_reduces_customer_balance(client, db):
    make_user(db, email="ventes_inv4@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_inv4@example.com")
    order, customer, product = _confirmed_order(client, headers, "INV4", qty=10, unit_price=100.0)
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=headers).json()
    client.post(f"/api/invoices/{invoice['id']}/validate", headers=headers)

    balance = client.get(f"/api/partners/{customer['id']}/balance", headers=headers).json()
    assert balance["balance"] == 1000.0

    credit_note = client.post(
        "/api/invoices/credit-notes",
        json={
            "origin_invoice_id": invoice["id"],
            "invoice_date": "2026-02-05",
            "lines": [{"product_id": product["id"], "qty": 2, "unit_price": 100.0}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/invoices/{credit_note['id']}/validate", headers=headers)

    balance = client.get(f"/api/partners/{customer['id']}/balance", headers=headers).json()
    assert balance["balance"] == 800.0  # 1000 - 200


def test_cannot_cancel_paid_invoice(client, db):
    make_user(db, email="ventes_inv5@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_inv5@example.com")
    order, _, _ = _confirmed_order(client, ventes_headers, "INV5", qty=10, unit_price=100.0)
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=ventes_headers).json()
    client.post(f"/api/invoices/{invoice['id']}/validate", headers=ventes_headers)

    make_user(db, email="caissier_inv5@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_inv5@example.com")
    payment = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 1000.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    client.post(f"/api/payments/{payment['id']}/confirm", headers=caissier_headers)

    resp = client.post(f"/api/invoices/{invoice['id']}/cancel", headers=ventes_headers)
    assert resp.status_code == 400


def test_cannot_credit_note_from_draft_invoice(client, db):
    make_user(db, email="ventes_inv6@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_inv6@example.com")
    order, _, product = _confirmed_order(client, headers, "INV6")
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=headers).json()
    resp = client.post(
        "/api/invoices/credit-notes",
        json={
            "origin_invoice_id": invoice["id"],
            "invoice_date": "2026-02-05",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 100.0}],
        },
        headers=headers,
    )
    assert resp.status_code == 400
