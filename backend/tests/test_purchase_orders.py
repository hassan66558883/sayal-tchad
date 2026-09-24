import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest import auth_headers, make_user


def _setup_supplier_and_product(client, headers):
    supplier = client.post(
        "/api/partners", json={"name": "Fournisseur PO", "is_supplier": True}, headers=headers
    ).json()
    uom_cat = client.post("/api/uom-categories", json={"name": "Unite PO"}, headers=headers).json()
    uom = client.post(
        "/api/uoms",
        json={"name": "Piece PO", "category_id": uom_cat["id"], "factor": 1.0, "is_reference": True},
        headers=headers,
    ).json()
    product = client.post("/api/products", json={"name": "Produit PO", "uom_id": uom["id"]}, headers=headers).json()
    return supplier, product


def test_create_purchase_order_with_lines_computes_total(client, db):
    make_user(db, email="achats_po1@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po1@example.com")
    supplier, product = _setup_supplier_and_product(client, headers)

    resp = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [{"product_id": product["id"], "qty": 10, "unit_price": 100.0}],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("ACH")
    assert body["state"] == "proforma"
    assert body["amount_total"] == 1000.0
    assert body["lines"][0]["subtotal"] == 1000.0


def test_cannot_confirm_order_without_lines(client, db):
    make_user(db, email="achats_po2@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po2@example.com")
    supplier, _ = _setup_supplier_and_product(client, headers)
    order = client.post(
        "/api/purchase-orders", json={"supplier_id": supplier["id"], "order_date": "2026-01-15"}, headers=headers
    ).json()
    resp = client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 400


def test_confirm_then_terminate_workflow(client, db):
    make_user(db, email="achats_po3@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po3@example.com")
    supplier, product = _setup_supplier_and_product(client, headers)
    order = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [{"product_id": product["id"], "qty": 5, "unit_price": 50.0}],
        },
        headers=headers,
    ).json()

    resp = client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    assert resp.json()["state"] == "commande"

    resp = client.post(f"/api/purchase-orders/{order['id']}/terminate", headers=headers)
    assert resp.json()["state"] == "terminee"


def test_cannot_terminate_proforma_order(client, db):
    make_user(db, email="achats_po4@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po4@example.com")
    supplier, product = _setup_supplier_and_product(client, headers)
    order = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 10.0}],
        },
        headers=headers,
    ).json()
    resp = client.post(f"/api/purchase-orders/{order['id']}/terminate", headers=headers)
    assert resp.status_code == 400


def test_cannot_confirm_twice(client, db):
    make_user(db, email="achats_po5@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po5@example.com")
    supplier, product = _setup_supplier_and_product(client, headers)
    order = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [{"product_id": product["id"], "qty": 1, "unit_price": 10.0}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    resp = client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=headers)
    assert resp.status_code == 400


def test_negative_qty_rejected_by_validation(client, db):
    make_user(db, email="achats_po6@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po6@example.com")
    supplier, product = _setup_supplier_and_product(client, headers)
    resp = client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-01-15",
            "lines": [{"product_id": product["id"], "qty": -1, "unit_price": 10.0}],
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_db_check_constraint_blocks_negative_qty_bypassing_pydantic(db):
    from app.models.partner import Partner
    from app.models.product import Product, Uom, UomCategory
    from app.models.purchase import PurchaseOrder, PurchaseOrderLine

    supplier = Partner(reference="TRSX01", name="Direct Supplier", is_supplier=True)
    uom_cat = UomCategory(name="UomX")
    db.add_all([supplier, uom_cat])
    db.flush()
    uom = Uom(name="PieceX", category_id=uom_cat.id, factor=1.0, is_reference=True)
    db.add(uom)
    db.flush()
    product = Product(reference="PRDX01", name="Direct Product", uom_id=uom.id)
    db.add(product)
    db.flush()
    order = PurchaseOrder(reference="ACHX01", supplier_id=supplier.id, order_date="2026-01-01", state="proforma")
    db.add(order)
    db.flush()
    line = PurchaseOrderLine(order_id=order.id, product_id=product.id, qty=-5, unit_price=10.0)
    db.add(line)
    with pytest.raises(IntegrityError):
        db.flush()


def test_supplier_must_actually_be_supplier(client, db):
    make_user(db, email="achats_po7@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_po7@example.com")
    customer = client.post(
        "/api/partners", json={"name": "Client pas fournisseur", "is_customer": True}, headers=headers
    ).json()
    resp = client.post(
        "/api/purchase-orders", json={"supplier_id": customer["id"], "order_date": "2026-01-15"}, headers=headers
    )
    assert resp.status_code == 400


def test_ventes_cannot_create_purchase_order(client, db):
    make_user(db, email="ventes_po1@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_po1@example.com")
    resp = client.post(
        "/api/purchase-orders", json={"supplier_id": 1, "order_date": "2026-01-15"}, headers=headers
    )
    assert resp.status_code == 403
