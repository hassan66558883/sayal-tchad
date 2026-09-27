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


def test_account_locks_after_five_failed_attempts(client, db):
    make_user(db, email="lockout1@example.com", password="correct-pass")
    for _ in range(5):
        resp = client.post("/api/auth/login", data={"username": "lockout1@example.com", "password": "wrong"})
        assert resp.status_code == 401

    # even the correct password is now refused - the account is locked
    resp = client.post("/api/auth/login", data={"username": "lockout1@example.com", "password": "correct-pass"})
    assert resp.status_code == 423


def test_successful_login_resets_failed_attempt_counter(client, db):
    make_user(db, email="lockout2@example.com", password="correct-pass")
    for _ in range(4):
        resp = client.post("/api/auth/login", data={"username": "lockout2@example.com", "password": "wrong"})
        assert resp.status_code == 401

    # one correct login before the 5th failure resets the counter
    resp = client.post("/api/auth/login", data={"username": "lockout2@example.com", "password": "correct-pass"})
    assert resp.status_code == 200

    for _ in range(4):
        resp = client.post("/api/auth/login", data={"username": "lockout2@example.com", "password": "wrong"})
        assert resp.status_code == 401
    # still not locked - only 4 failures since the reset
    resp = client.post("/api/auth/login", data={"username": "lockout2@example.com", "password": "correct-pass"})
    assert resp.status_code == 200
