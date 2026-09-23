from tests.conftest import auth_headers, make_user


def test_login_succeeds_with_correct_password(client, db):
    make_user(db, email="login_ok@example.com", password="correct-pass")
    resp = client.post("/api/auth/login", data={"username": "login_ok@example.com", "password": "correct-pass"})
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"]


def test_login_fails_with_wrong_password(client, db):
    make_user(db, email="login_bad@example.com", password="correct-pass")
    resp = client.post("/api/auth/login", data={"username": "login_bad@example.com", "password": "wrong-pass"})
    assert resp.status_code == 401


def test_login_fails_for_unknown_email(client):
    resp = client.post("/api/auth/login", data={"username": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


def test_login_fails_for_inactive_user(client, db):
    user = make_user(db, email="inactive@example.com", password="correct-pass")
    user.active = False
    db.commit()
    resp = client.post("/api/auth/login", data={"username": "inactive@example.com", "password": "correct-pass"})
    assert resp.status_code == 401


def test_me_returns_current_user(client, db):
    make_user(db, name="Alice", email="alice_me@example.com", password="correct-pass")
    headers = auth_headers(client, "alice_me@example.com", "correct-pass")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice_me@example.com"
    assert resp.json()["name"] == "Alice"


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_login_updates_last_login_at(client, db):
    make_user(db, email="lastlogin@example.com", password="correct-pass")
    headers = auth_headers(client, "lastlogin@example.com", "correct-pass")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.json()["email"] == "lastlogin@example.com"
