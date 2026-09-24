from tests.conftest import auth_headers, make_user


def _create_uom_category(client, headers, name="Poids"):
    return client.post("/api/uom-categories", json={"name": name}, headers=headers).json()


def _create_uom(client, headers, category_id, name, factor, is_reference=False):
    return client.post(
        "/api/uoms",
        json={"name": name, "category_id": category_id, "factor": factor, "is_reference": is_reference},
        headers=headers,
    ).json()


def test_achats_can_create_category_and_product(client, db):
    make_user(db, email="achats1@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats1@example.com")

    category = client.post(
        "/api/product-categories", json={"name": "Boissons", "code": "BOI"}, headers=headers
    ).json()
    uom_cat = _create_uom_category(client, headers, "Volume")
    kg = _create_uom(client, headers, uom_cat["id"], "Litre", 1.0, is_reference=True)

    resp = client.post(
        "/api/products",
        json={"name": "Eau minerale 1.5L", "category_id": category["id"], "uom_id": kg["id"], "sale_price": 500},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("PRD")
    assert body["sale_price"] == 500


def test_product_references_are_sequential(client, db):
    make_user(db, email="achats2@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats2@example.com")
    uom_cat = _create_uom_category(client, headers, "Unite")
    unit = _create_uom(client, headers, uom_cat["id"], "Piece", 1.0, is_reference=True)

    p1 = client.post("/api/products", json={"name": "Produit A", "uom_id": unit["id"]}, headers=headers).json()
    p2 = client.post("/api/products", json={"name": "Produit B", "uom_id": unit["id"]}, headers=headers).json()
    n1 = int(p1["reference"][3:])
    n2 = int(p2["reference"][3:])
    assert n2 == n1 + 1


def test_ventes_role_cannot_create_product(client, db):
    make_user(db, email="ventes_prod@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_prod@example.com")
    resp = client.post("/api/products", json={"name": "X", "uom_id": 1}, headers=headers)
    assert resp.status_code == 403


def test_duplicate_barcode_rejected(client, db):
    make_user(db, email="achats3@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats3@example.com")
    uom_cat = _create_uom_category(client, headers, "Unite2")
    unit = _create_uom(client, headers, uom_cat["id"], "Piece2", 1.0, is_reference=True)

    client.post(
        "/api/products", json={"name": "P1", "uom_id": unit["id"], "barcode": "1234567890123"}, headers=headers
    )
    resp = client.post(
        "/api/products", json={"name": "P2", "uom_id": unit["id"], "barcode": "1234567890123"}, headers=headers
    )
    assert resp.status_code == 400


def test_uom_conversion_sac_to_kilogramme():
    from app.models.product import Uom, UomCategory
    from app.services.uom import convert_qty

    category = UomCategory(id=1, name="Poids")
    kg = Uom(id=1, name="Kilogramme", category_id=1, factor=1.0, is_reference=True)
    sac = Uom(id=2, name="Sac de 50 kg", category_id=1, factor=50.0, is_reference=False)

    assert convert_qty(1, sac, kg) == 50.0
    assert convert_qty(100, kg, sac) == 2.0


def test_uom_conversion_rejects_different_categories():
    import pytest
    from fastapi import HTTPException

    from app.models.product import Uom
    from app.services.uom import convert_qty

    weight = Uom(id=1, name="Kilogramme", category_id=1, factor=1.0)
    volume = Uom(id=2, name="Litre", category_id=2, factor=1.0)
    with pytest.raises(HTTPException):
        convert_qty(1, weight, volume)


def test_anyone_authenticated_can_list_products(client, db):
    make_user(db, email="achats4@example.com", role_codes=["achats"])
    achats_headers = auth_headers(client, "achats4@example.com")
    uom_cat = _create_uom_category(client, achats_headers, "Unite3")
    unit = _create_uom(client, achats_headers, uom_cat["id"], "Piece3", 1.0, is_reference=True)
    client.post("/api/products", json={"name": "Visible", "uom_id": unit["id"]}, headers=achats_headers)

    make_user(db, email="chauffeur_prod@example.com", role_codes=["chauffeur"])
    headers = auth_headers(client, "chauffeur_prod@example.com")
    resp = client.get("/api/products", headers=headers)
    assert resp.status_code == 200
    assert any(p["name"] == "Visible" for p in resp.json())
