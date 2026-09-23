from tests.conftest import auth_headers, make_user


def test_direction_generale_can_create_branch(client, db):
    make_user(db, email="dg_branch@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_branch@example.com")
    resp = client.post("/api/branches", json={"name": "Agence Ndjamena", "code": "NDJ"}, headers=headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["code"] == "NDJ"


def test_non_direction_generale_cannot_create_branch(client, db):
    make_user(db, email="ventes_branch@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_branch@example.com")
    resp = client.post("/api/branches", json={"name": "Agence Moundou", "code": "MOU"}, headers=headers)
    assert resp.status_code == 403


def test_create_branch_rejects_duplicate_code(client, db):
    make_user(db, email="dg_dup@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_dup@example.com")
    client.post("/api/branches", json={"name": "Agence Sarh", "code": "SAR"}, headers=headers)
    resp = client.post("/api/branches", json={"name": "Agence Sarh 2", "code": "SAR"}, headers=headers)
    assert resp.status_code == 400


def test_responsable_agence_without_branch_sees_nothing(client, db):
    make_user(db, email="resp_none@example.com", role_codes=["responsable_agence"])
    headers = auth_headers(client, "resp_none@example.com")
    resp = client.get("/api/branches", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_responsable_agence_sees_only_own_branch(client, db):
    dg = make_user(db, email="dg_setup@example.com", role_codes=["direction_generale"])
    dg_headers = auth_headers(client, "dg_setup@example.com")
    b1 = client.post("/api/branches", json={"name": "Agence A", "code": "A1"}, headers=dg_headers).json()
    client.post("/api/branches", json={"name": "Agence B", "code": "B1"}, headers=dg_headers)

    from app.models.company import Branch

    resp_user = make_user(db, email="resp_scoped@example.com", role_codes=["responsable_agence"])
    branch_row = db.query(Branch).filter(Branch.code == "A1").one()
    resp_user.branches.append(branch_row)
    db.commit()

    resp_headers = auth_headers(client, "resp_scoped@example.com")
    resp = client.get("/api/branches", headers=resp_headers)
    assert resp.status_code == 200
    codes = {b["code"] for b in resp.json()}
    assert codes == {"A1"}


def test_ventes_role_sees_all_branches(client, db):
    make_user(db, email="dg_all@example.com", role_codes=["direction_generale"])
    dg_headers = auth_headers(client, "dg_all@example.com")
    client.post("/api/branches", json={"name": "Agence C", "code": "C1"}, headers=dg_headers)
    client.post("/api/branches", json={"name": "Agence D", "code": "D1"}, headers=dg_headers)

    make_user(db, email="ventes_all@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_all@example.com")
    resp = client.get("/api/branches", headers=headers)
    codes = {b["code"] for b in resp.json()}
    assert {"C1", "D1"}.issubset(codes)
