from tests.conftest import auth_headers, make_user

FINANCE_ROLES = ["comptable", "achats", "ventes", "stock", "caissier"]


def _setup_confirmed_purchase_order(client, headers, code, qty=10, unit_price=100.0):
    supplier = client.post(
        "/api/partners", json={"name": f"Fournisseur {code}", "is_supplier": True}, headers=headers
    ).json()
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
            "order_date": "2026-04-01",
            "lines": [{"product_id": product["id"], "qty": qty, "unit_price": unit_price}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 200, resp.text
    return supplier, resp.json()


def test_supplier_invoice_from_order_and_full_payment_via_cash(client, db):
    make_user(db, email="fin1@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin1@example.com")
    supplier, order = _setup_confirmed_purchase_order(client, headers, "F1", qty=5, unit_price=200.0)

    invoice = client.post(
        "/api/supplier-invoices/from-order", json={"purchase_order_id": order["id"]}, headers=headers
    ).json()
    assert invoice["reference"].startswith("FRS")
    assert invoice["amount_total"] == 1000.0
    assert invoice["payment_state"] == "not_paid"

    validate_resp = client.post(f"/api/supplier-invoices/{invoice['id']}/validate", headers=headers)
    assert validate_resp.status_code == 200

    register = client.post("/api/cash-registers", json={"name": "Caisse F1", "code": "CR-F1"}, headers=headers).json()
    session = client.post("/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 0.0}, headers=headers).json()
    assert session["state"] == "open"
    assert session["computed_balance"] == 0.0

    payment = client.post(
        "/api/supplier-payments",
        json={
            "invoice_id": invoice["id"],
            "amount": 1000.0,
            "payment_date": "2026-04-05",
            "payment_method": "especes",
            "cash_session_id": session["id"],
        },
        headers=headers,
    ).json()
    confirm_resp = client.post(f"/api/supplier-payments/{payment['id']}/confirm", headers=headers)
    assert confirm_resp.status_code == 200, confirm_resp.text

    invoice = client.get(f"/api/supplier-invoices/{invoice['id']}", headers=headers).json()
    assert invoice["payment_state"] == "paid"
    assert invoice["amount_due"] == 0.0

    balance = client.get(f"/api/partners/{supplier['id']}/supplier-balance", headers=headers).json()["balance"]
    assert balance == 0.0

    session_after = client.get("/api/cash-sessions", headers=headers).json()
    this_session = next(s for s in session_after if s["id"] == session["id"])
    assert this_session["computed_balance"] == -1000.0


def test_supplier_payment_cannot_exceed_amount_due(client, db):
    make_user(db, email="fin2@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin2@example.com")
    supplier, order = _setup_confirmed_purchase_order(client, headers, "F2", qty=1, unit_price=100.0)
    invoice = client.post("/api/supplier-invoices/from-order", json={"purchase_order_id": order["id"]}, headers=headers).json()
    client.post(f"/api/supplier-invoices/{invoice['id']}/validate", headers=headers)

    account = client.post(
        "/api/bank-accounts",
        json={"name": "Compte F2", "bank_name": "Banque Tchad", "account_number": "ACC-F2"},
        headers=headers,
    ).json()

    payment1 = client.post(
        "/api/supplier-payments",
        json={"invoice_id": invoice["id"], "amount": 60.0, "payment_date": "2026-04-05", "payment_method": "banque", "bank_account_id": account["id"]},
        headers=headers,
    ).json()
    assert client.post(f"/api/supplier-payments/{payment1['id']}/confirm", headers=headers).status_code == 200

    payment2 = client.post(
        "/api/supplier-payments",
        json={"invoice_id": invoice["id"], "amount": 60.0, "payment_date": "2026-04-06", "payment_method": "banque", "bank_account_id": account["id"]},
        headers=headers,
    ).json()
    resp = client.post(f"/api/supplier-payments/{payment2['id']}/confirm", headers=headers)
    assert resp.status_code == 400


def test_two_partial_supplier_payments_summing_exactly_to_total_both_succeed(client, db):
    make_user(db, email="fin3@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin3@example.com")
    _, order = _setup_confirmed_purchase_order(client, headers, "F3", qty=1, unit_price=100.0)
    invoice = client.post("/api/supplier-invoices/from-order", json={"purchase_order_id": order["id"]}, headers=headers).json()
    client.post(f"/api/supplier-invoices/{invoice['id']}/validate", headers=headers)

    account = client.post(
        "/api/bank-accounts", json={"name": "Compte F3", "bank_name": "Banque Tchad", "account_number": "ACC-F3"}, headers=headers
    ).json()

    for amount in (50.0, 50.0):
        payment = client.post(
            "/api/supplier-payments",
            json={"invoice_id": invoice["id"], "amount": amount, "payment_date": "2026-04-05", "payment_method": "banque", "bank_account_id": account["id"]},
            headers=headers,
        ).json()
        resp = client.post(f"/api/supplier-payments/{payment['id']}/confirm", headers=headers)
        assert resp.status_code == 200, resp.text

    invoice = client.get(f"/api/supplier-invoices/{invoice['id']}", headers=headers).json()
    assert invoice["payment_state"] == "paid"


def test_bank_account_balance_reflects_transactions_and_payments(client, db):
    make_user(db, email="fin4@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin4@example.com")
    account = client.post(
        "/api/bank-accounts",
        json={"name": "Compte F4", "bank_name": "Banque Tchad", "account_number": "ACC-F4", "opening_balance": 5000.0},
        headers=headers,
    ).json()
    assert account["balance"] == 5000.0

    client.post(
        "/api/bank-transactions",
        json={"bank_account_id": account["id"], "movement_type": "in", "amount": 2000.0, "transaction_date": "2026-04-01", "reason": "Apport"},
        headers=headers,
    )
    client.post(
        "/api/bank-transactions",
        json={"bank_account_id": account["id"], "movement_type": "out", "amount": 500.0, "transaction_date": "2026-04-02", "reason": "Frais bancaires"},
        headers=headers,
    )
    accounts = client.get("/api/bank-accounts", headers=headers).json()
    updated = next(a for a in accounts if a["id"] == account["id"])
    assert updated["balance"] == 6500.0


def test_expense_paid_from_cash_session_reduces_computed_balance(client, db):
    make_user(db, email="fin5@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin5@example.com")
    register = client.post("/api/cash-registers", json={"name": "Caisse F5", "code": "CR-F5"}, headers=headers).json()
    session = client.post(
        "/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 1000.0}, headers=headers
    ).json()

    expense = client.post(
        "/api/expenses",
        json={
            "category": "Carburant",
            "amount": 150.0,
            "expense_date": "2026-04-03",
            "payment_method": "especes",
            "cash_session_id": session["id"],
        },
        headers=headers,
    ).json()
    assert expense["reference"].startswith("DEP")
    assert expense["state"] == "draft"

    sessions = client.get("/api/cash-sessions", headers=headers).json()
    unvalidated = next(s for s in sessions if s["id"] == session["id"])
    assert unvalidated["computed_balance"] == 1000.0  # draft expense doesn't count yet

    validate_resp = client.post(f"/api/expenses/{expense['id']}/validate", headers=headers)
    assert validate_resp.status_code == 200

    sessions = client.get("/api/cash-sessions", headers=headers).json()
    validated = next(s for s in sessions if s["id"] == session["id"])
    assert validated["computed_balance"] == 850.0


def test_expense_requires_open_cash_session_when_paid_in_cash(client, db):
    make_user(db, email="fin6@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin6@example.com")
    resp = client.post(
        "/api/expenses",
        json={"category": "Fournitures", "amount": 20.0, "expense_date": "2026-04-03", "payment_method": "especes"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_closing_cash_session_records_variance(client, db):
    make_user(db, email="fin7@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin7@example.com")
    register = client.post("/api/cash-registers", json={"name": "Caisse F7", "code": "CR-F7"}, headers=headers).json()
    session = client.post(
        "/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 100.0}, headers=headers
    ).json()

    resp = client.post(f"/api/cash-sessions/{session['id']}/close", json={"closing_balance": 90.0}, headers=headers)
    assert resp.status_code == 200
    closed = resp.json()
    assert closed["state"] == "closed"
    assert closed["computed_balance"] == 100.0
    assert closed["variance"] == -10.0


def test_cannot_open_two_sessions_on_same_register(client, db):
    make_user(db, email="fin8@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin8@example.com")
    register = client.post("/api/cash-registers", json={"name": "Caisse F8", "code": "CR-F8"}, headers=headers).json()
    client.post("/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 0.0}, headers=headers)
    resp = client.post("/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 0.0}, headers=headers)
    assert resp.status_code == 400


def test_cannot_pay_via_cash_session_that_is_closed(client, db):
    make_user(db, email="fin9@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin9@example.com")
    _, order = _setup_confirmed_purchase_order(client, headers, "F9", qty=1, unit_price=100.0)
    invoice = client.post("/api/supplier-invoices/from-order", json={"purchase_order_id": order["id"]}, headers=headers).json()
    client.post(f"/api/supplier-invoices/{invoice['id']}/validate", headers=headers)

    register = client.post("/api/cash-registers", json={"name": "Caisse F9", "code": "CR-F9"}, headers=headers).json()
    session = client.post("/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 0.0}, headers=headers).json()
    client.post(f"/api/cash-sessions/{session['id']}/close", json={"closing_balance": 0.0}, headers=headers)

    resp = client.post(
        "/api/supplier-payments",
        json={"invoice_id": invoice["id"], "amount": 100.0, "payment_date": "2026-04-05", "payment_method": "especes", "cash_session_id": session["id"]},
        headers=headers,
    )
    assert resp.status_code == 400


def test_debit_note_reduces_supplier_balance(client, db):
    make_user(db, email="fin10@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin10@example.com")
    supplier, order = _setup_confirmed_purchase_order(client, headers, "F10", qty=2, unit_price=500.0)
    invoice = client.post("/api/supplier-invoices/from-order", json={"purchase_order_id": order["id"]}, headers=headers).json()
    client.post(f"/api/supplier-invoices/{invoice['id']}/validate", headers=headers)

    balance_before = client.get(f"/api/partners/{supplier['id']}/supplier-balance", headers=headers).json()["balance"]
    assert balance_before == 1000.0

    product_id = invoice["lines"][0]["product_id"]
    debit_note = client.post(
        "/api/supplier-invoices/debit-notes",
        json={
            "origin_invoice_id": invoice["id"],
            "invoice_date": "2026-04-10",
            "lines": [{"product_id": product_id, "qty": 1, "unit_price": 500.0}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/supplier-invoices/{debit_note['id']}/validate", headers=headers)

    balance_after = client.get(f"/api/partners/{supplier['id']}/supplier-balance", headers=headers).json()["balance"]
    assert balance_after == 500.0


def test_stock_role_cannot_manage_cash_registers_or_bank_accounts(client, db):
    make_user(db, email="stock_fin1@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock_fin1@example.com")
    resp = client.post("/api/cash-registers", json={"name": "X", "code": "CR-X"}, headers=headers)
    assert resp.status_code == 403
    resp = client.post(
        "/api/bank-accounts", json={"name": "X", "bank_name": "X", "account_number": "X"}, headers=headers
    )
    assert resp.status_code == 403


def test_only_finance_managers_can_validate_expense(client, db):
    make_user(db, email="fin11@example.com", role_codes=FINANCE_ROLES)
    headers = auth_headers(client, "fin11@example.com")
    register = client.post("/api/cash-registers", json={"name": "Caisse F11", "code": "CR-F11"}, headers=headers).json()
    session = client.post("/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 0.0}, headers=headers).json()
    expense = client.post(
        "/api/expenses",
        json={"category": "Divers", "amount": 10.0, "expense_date": "2026-04-03", "payment_method": "especes", "cash_session_id": session["id"]},
        headers=headers,
    ).json()

    make_user(db, email="caissier_only@example.com", role_codes=["caissier"])
    cashier_headers = auth_headers(client, "caissier_only@example.com")
    resp = client.post(f"/api/expenses/{expense['id']}/validate", headers=cashier_headers)
    assert resp.status_code == 403
