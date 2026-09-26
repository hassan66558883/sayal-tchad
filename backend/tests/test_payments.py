from tests.conftest import auth_headers, make_user


def _validated_invoice(client, ventes_headers, code="PAY", qty=10, unit_price=100.0):
    customer = client.post("/api/partners", json={"name": f"Client {code}", "is_customer": True}, headers=ventes_headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": f"Unite {code}"}, headers=ventes_headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": f"Piece {code}", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=ventes_headers,
    ).json()
    product = client.post("/api/products", json={"name": f"Produit {code}", "uom_id": uom["id"]}, headers=ventes_headers).json()
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": qty, "unit_price": unit_price}],
        },
        headers=ventes_headers,
    ).json()
    client.post(f"/api/sale-orders/{order['id']}/confirm", headers=ventes_headers)
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=ventes_headers).json()
    client.post(f"/api/invoices/{invoice['id']}/validate", headers=ventes_headers)
    return invoice, customer


def test_partial_payment_updates_payment_state(client, db):
    make_user(db, email="ventes_pay1@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay1@example.com")
    invoice, _ = _validated_invoice(client, ventes_headers, "PAY1", qty=10, unit_price=100.0)

    make_user(db, email="caissier_pay1@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay1@example.com")
    payment = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 400.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    client.post(f"/api/payments/{payment['id']}/confirm", headers=caissier_headers)

    resp = client.get(f"/api/invoices/{invoice['id']}", headers=ventes_headers)
    body = resp.json()
    assert body["amount_paid"] == 400.0
    assert body["amount_due"] == 600.0
    assert body["payment_state"] == "partially_paid"


def test_full_payment_marks_invoice_paid(client, db):
    make_user(db, email="ventes_pay2@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay2@example.com")
    invoice, _ = _validated_invoice(client, ventes_headers, "PAY2", qty=5, unit_price=100.0)

    make_user(db, email="caissier_pay2@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay2@example.com")
    payment = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 500.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    client.post(f"/api/payments/{payment['id']}/confirm", headers=caissier_headers)

    resp = client.get(f"/api/invoices/{invoice['id']}", headers=ventes_headers)
    assert resp.json()["payment_state"] == "paid"


def test_two_partial_payments_summing_exactly_to_total_both_succeed(client, db):
    """Regression guard for the self-counting overpayment bug from the
    prior Odoo-based build: confirming a payment must compare against
    OTHER confirmed payments, not a stale total that already includes
    itself - otherwise the second of two payments that exactly sum to
    the invoice total would be wrongly rejected.
    """
    make_user(db, email="ventes_pay3@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay3@example.com")
    invoice, _ = _validated_invoice(client, ventes_headers, "PAY3", qty=10, unit_price=100.0)

    make_user(db, email="caissier_pay3@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay3@example.com")

    p1 = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 600.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    resp1 = client.post(f"/api/payments/{p1['id']}/confirm", headers=caissier_headers)
    assert resp1.status_code == 200

    p2 = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 400.0, "payment_date": "2026-02-11"},
        headers=caissier_headers,
    ).json()
    resp2 = client.post(f"/api/payments/{p2['id']}/confirm", headers=caissier_headers)
    assert resp2.status_code == 200

    resp = client.get(f"/api/invoices/{invoice['id']}", headers=ventes_headers)
    assert resp.json()["payment_state"] == "paid"
    assert resp.json()["amount_due"] == 0.0


def test_overpayment_rejected(client, db):
    make_user(db, email="ventes_pay4@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay4@example.com")
    invoice, _ = _validated_invoice(client, ventes_headers, "PAY4", qty=5, unit_price=100.0)

    make_user(db, email="caissier_pay4@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay4@example.com")
    payment = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 600.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    resp = client.post(f"/api/payments/{payment['id']}/confirm", headers=caissier_headers)
    assert resp.status_code == 400


def test_overpayment_rejected_after_partial_payment(client, db):
    make_user(db, email="ventes_pay5@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay5@example.com")
    invoice, _ = _validated_invoice(client, ventes_headers, "PAY5", qty=10, unit_price=100.0)

    make_user(db, email="caissier_pay5@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay5@example.com")
    p1 = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 700.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    client.post(f"/api/payments/{p1['id']}/confirm", headers=caissier_headers)

    p2 = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 400.0, "payment_date": "2026-02-11"},
        headers=caissier_headers,
    ).json()
    resp = client.post(f"/api/payments/{p2['id']}/confirm", headers=caissier_headers)
    assert resp.status_code == 400


def test_confirmed_payment_cannot_be_cancelled(client, db):
    make_user(db, email="ventes_pay6@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay6@example.com")
    invoice, _ = _validated_invoice(client, ventes_headers, "PAY6", qty=1, unit_price=100.0)

    make_user(db, email="caissier_pay6@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay6@example.com")
    payment = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 100.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    ).json()
    client.post(f"/api/payments/{payment['id']}/confirm", headers=caissier_headers)
    resp = client.post(f"/api/payments/{payment['id']}/cancel", headers=caissier_headers)
    assert resp.status_code == 400


def test_ventes_role_cannot_create_payment(client, db):
    make_user(db, email="ventes_pay7@example.com", role_codes=["ventes", "achats"])
    headers = auth_headers(client, "ventes_pay7@example.com")
    invoice, _ = _validated_invoice(client, headers, "PAY7", qty=1, unit_price=100.0)
    resp = client.post(
        "/api/payments", json={"invoice_id": invoice["id"], "amount": 100.0, "payment_date": "2026-02-10"}, headers=headers
    )
    assert resp.status_code == 403


def test_cannot_pay_draft_invoice(client, db):
    make_user(db, email="ventes_pay8@example.com", role_codes=["ventes", "achats"])
    ventes_headers = auth_headers(client, "ventes_pay8@example.com")
    customer = client.post("/api/partners", json={"name": "Client Draft", "is_customer": True}, headers=ventes_headers).json()
    uom_cat = client.post("/api/uom-categories", json={"name": "Unite Draft"}, headers=ventes_headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": "Piece Draft", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=ventes_headers,
    ).json()
    product = client.post("/api/products", json={"name": "Produit Draft", "uom_id": uom["id"]}, headers=ventes_headers).json()
    order = client.post(
        "/api/sale-orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-02-01",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 100.0}],
        },
        headers=ventes_headers,
    ).json()
    client.post(f"/api/sale-orders/{order['id']}/confirm", headers=ventes_headers)
    invoice = client.post("/api/invoices/from-order", json={"sale_order_id": order["id"]}, headers=ventes_headers).json()

    make_user(db, email="caissier_pay8@example.com", role_codes=["caissier"])
    caissier_headers = auth_headers(client, "caissier_pay8@example.com")
    resp = client.post(
        "/api/payments",
        json={"invoice_id": invoice["id"], "amount": 100.0, "payment_date": "2026-02-10"},
        headers=caissier_headers,
    )
    assert resp.status_code == 400
