from tests.conftest import auth_headers, make_user


def test_ventes_can_create_customer(client, db):
    make_user(db, email="ventes_p1@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_p1@example.com")
    resp = client.post(
        "/api/partners",
        json={"name": "Client Grossiste SARL", "is_customer": True, "customer_type": "grossiste"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("TRS")
    assert body["is_customer"] is True


def test_achats_can_create_supplier(client, db):
    make_user(db, email="achats_p1@example.com", role_codes=["achats"])
    headers = auth_headers(client, "achats_p1@example.com")
    resp = client.post(
        "/api/partners", json={"name": "Fournisseur Import SA", "is_supplier": True}, headers=headers
    )
    assert resp.status_code == 201


def test_partner_must_be_customer_or_supplier(client, db):
    make_user(db, email="ventes_p2@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_p2@example.com")
    resp = client.post("/api/partners", json={"name": "Ni l'un ni l'autre"}, headers=headers)
    assert resp.status_code == 400


def test_invalid_customer_type_rejected(client, db):
    make_user(db, email="ventes_p3@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_p3@example.com")
    resp = client.post(
        "/api/partners",
        json={"name": "X", "is_customer": True, "customer_type": "pas_un_vrai_type"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_chauffeur_cannot_create_partner(client, db):
    make_user(db, email="chauffeur_p1@example.com", role_codes=["chauffeur"])
    headers = auth_headers(client, "chauffeur_p1@example.com")
    resp = client.post("/api/partners", json={"name": "X", "is_customer": True}, headers=headers)
    assert resp.status_code == 403


def test_filter_customers_only(client, db):
    make_user(db, email="ventes_p4@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_p4@example.com")
    client.post("/api/partners", json={"name": "Client Filtre", "is_customer": True}, headers=headers)
    client.post("/api/partners", json={"name": "Fournisseur Filtre", "is_supplier": True}, headers=headers)

    resp = client.get("/api/partners", params={"is_customer": True}, headers=headers)
    names = {p["name"] for p in resp.json()}
    assert "Client Filtre" in names
    assert "Fournisseur Filtre" not in names


def test_responsable_agence_sees_only_own_branch_partners(client, db):
    from app.models.company import Branch

    dg = make_user(db, email="dg_p1@example.com", role_codes=["direction_generale"])
    dg_headers = auth_headers(client, "dg_p1@example.com")
    branch = client.post("/api/branches", json={"name": "Agence P1", "code": "AGP1"}, headers=dg_headers).json()

    client.post(
        "/api/partners",
        json={"name": "Client Agence P1", "is_customer": True, "branch_id": branch["id"]},
        headers=dg_headers,
    )
    client.post("/api/partners", json={"name": "Client Sans Agence", "is_customer": True}, headers=dg_headers)

    resp_user = make_user(db, email="resp_p1@example.com", role_codes=["responsable_agence"])
    branch_row = db.query(Branch).filter(Branch.code == "AGP1").one()
    resp_user.branches.append(branch_row)
    db.commit()

    resp_headers = auth_headers(client, "resp_p1@example.com")
    resp = client.get("/api/partners", headers=resp_headers)
    names = {p["name"] for p in resp.json()}
    assert names == {"Client Agence P1"}
