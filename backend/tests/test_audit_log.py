from tests.conftest import auth_headers, make_user


def test_creating_branch_writes_audit_log_entry(client, db):
    make_user(db, email="dg_audit@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_audit@example.com")
    branch = client.post("/api/branches", json={"name": "Agence Audit", "code": "AUD1"}, headers=headers).json()

    resp = client.get("/api/audit-logs", params={"model_name": "branches", "record_id": branch["id"]}, headers=headers)
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "create"
    assert entries[0]["record_name"] == "Agence Audit"


def test_updating_branch_writes_audit_log_entry(client, db):
    make_user(db, email="dg_audit2@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_audit2@example.com")
    branch = client.post("/api/branches", json={"name": "Agence Audit2", "code": "AUD2"}, headers=headers).json()
    client.patch(f"/api/branches/{branch['id']}", json={"city": "Ndjamena"}, headers=headers)

    resp = client.get("/api/audit-logs", params={"model_name": "branches", "record_id": branch["id"]}, headers=headers)
    actions = [e["action"] for e in resp.json()]
    assert actions.count("create") == 1
    assert actions.count("update") == 1


def test_audit_log_attributes_action_to_acting_user(client, db):
    dg = make_user(db, email="dg_audit3@example.com", role_codes=["direction_generale"])
    headers = auth_headers(client, "dg_audit3@example.com")
    branch = client.post("/api/branches", json={"name": "Agence Audit3", "code": "AUD3"}, headers=headers).json()

    resp = client.get("/api/audit-logs", params={"model_name": "branches", "record_id": branch["id"]}, headers=headers)
    assert resp.json()[0]["user_id"] == dg.id


def test_audit_logs_require_direction_generale(client, db):
    make_user(db, email="ventes_audit@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "ventes_audit@example.com")
    resp = client.get("/api/audit-logs", headers=headers)
    assert resp.status_code == 403
