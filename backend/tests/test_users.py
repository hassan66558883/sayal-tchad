from tests.conftest import auth_headers, make_user


def test_direction_generale_can_create_user_with_roles(client, db):
    make_user(db, email="dg_users@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_users@example.com")
    resp = client.post(
        "/api/users",
        json={"name": "Nouveau Vendeur", "email": "vendeur1@example.com", "password": "pass1234", "role_codes": ["ventes"]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "vendeur1@example.com"
    assert [r["code"] for r in body["roles"]] == ["ventes"]


def test_create_user_rejects_duplicate_email(client, db):
    make_user(db, email="dg_users2@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_users2@example.com")
    payload = {"name": "Dup", "email": "dup_user@example.com", "password": "pass1234", "role_codes": []}
    client.post("/api/users", json=payload, headers=headers)
    resp = client.post("/api/users", json=payload, headers=headers)
    assert resp.status_code == 400


def test_create_user_rejects_unknown_role_code(client, db):
    make_user(db, email="dg_users3@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_users3@example.com")
    resp = client.post(
        "/api/users",
        json={"name": "X", "email": "userx@example.com", "password": "pass1234", "role_codes": ["not_a_real_role"]},
        headers=headers,
    )
    assert resp.status_code == 400


def test_non_direction_generale_cannot_list_users(client, db):
    make_user(db, email="ventes_users@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_users@example.com")
    resp = client.get("/api/users", headers=headers)
    assert resp.status_code == 403


def test_user_can_read_own_profile_without_direction_generale(client, db):
    user = make_user(db, email="self_read@example.com", role_codes=["chauffeur"])
    headers = auth_headers(client, "self_read@example.com")
    resp = client.get(f"/api/users/{user.id}", headers=headers)
    assert resp.status_code == 200


def test_user_cannot_read_other_users_profile(client, db):
    make_user(db, email="reader@example.com", role_codes=["chauffeur"])
    other = make_user(db, email="other_person@example.com", role_codes=["chauffeur"])
    headers = auth_headers(client, "reader@example.com")
    resp = client.get(f"/api/users/{other.id}", headers=headers)
    assert resp.status_code == 403


def test_superuser_bypasses_role_check(client, db):
    make_user(db, email="root_user@example.com", is_superuser=True)
    headers = auth_headers(client, "root_user@example.com")
    resp = client.get("/api/users", headers=headers)
    assert resp.status_code == 200
