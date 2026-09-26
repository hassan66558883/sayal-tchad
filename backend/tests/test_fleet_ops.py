from datetime import date, timedelta

from tests.conftest import auth_headers, make_user

FLEET_ROLES = ["logistique", "comptable", "caissier"]


def _setup_vehicle(client, headers, code):
    return client.post("/api/vehicles", json={"name": f"Camion {code}", "plate_number": f"TCH-{code}"}, headers=headers).json()


def test_fuel_log_requires_cash_session_when_paid_in_cash(client, db):
    make_user(db, email="fleet1@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet1@example.com")
    vehicle = _setup_vehicle(client, headers, "FL1")
    resp = client.post(
        "/api/fuel-logs",
        json={"vehicle_id": vehicle["id"], "log_date": "2026-05-01", "liters": 50, "unit_price": 10, "payment_method": "especes"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_fuel_log_total_cost_computed_and_summed_across_logs(client, db):
    make_user(db, email="fleet2@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet2@example.com")
    vehicle = _setup_vehicle(client, headers, "FL2")
    register = client.post("/api/cash-registers", json={"name": "Caisse FL2", "code": "CR-FL2"}, headers=headers).json()
    session = client.post("/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 0}, headers=headers).json()

    log1 = client.post(
        "/api/fuel-logs",
        json={
            "vehicle_id": vehicle["id"],
            "log_date": "2026-05-01",
            "liters": 50,
            "unit_price": 10,
            "payment_method": "especes",
            "cash_session_id": session["id"],
        },
        headers=headers,
    ).json()
    assert log1["total_cost"] == 500.0

    client.post(
        "/api/fuel-logs",
        json={
            "vehicle_id": vehicle["id"],
            "log_date": "2026-05-05",
            "liters": 30,
            "unit_price": 12,
            "payment_method": "especes",
            "cash_session_id": session["id"],
        },
        headers=headers,
    )

    resp = client.get(f"/api/vehicles/{vehicle['id']}/fuel-cost", headers=headers)
    assert resp.json()["total_fuel_cost"] == 860.0  # 500 + 360

    sessions = client.get("/api/cash-sessions", headers=headers).json()
    this_session = next(s for s in sessions if s["id"] == session["id"])
    # a fuel purchase paid in cash is real money leaving the register, same as an expense
    assert this_session["computed_balance"] == -860.0


def test_vehicle_maintenance_workflow(client, db):
    make_user(db, email="fleet3@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet3@example.com")
    vehicle = _setup_vehicle(client, headers, "FL3")
    account = client.post(
        "/api/bank-accounts", json={"name": "Compte FL3", "bank_name": "Banque Tchad", "account_number": "ACC-FL3"}, headers=headers
    ).json()

    maintenance = client.post(
        "/api/vehicle-maintenances",
        json={
            "vehicle_id": vehicle["id"],
            "maintenance_date": "2026-05-02",
            "description": "Vidange",
            "cost": 200,
            "payment_method": "banque",
            "bank_account_id": account["id"],
        },
        headers=headers,
    ).json()
    assert maintenance["state"] == "planifiee"

    resp = client.get(f"/api/vehicles/{vehicle['id']}/maintenance-cost", headers=headers)
    assert resp.json()["total_maintenance_cost"] == 0.0  # not completed yet

    complete_resp = client.post(f"/api/vehicle-maintenances/{maintenance['id']}/complete", headers=headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["state"] == "terminee"

    resp = client.get(f"/api/vehicles/{vehicle['id']}/maintenance-cost", headers=headers)
    assert resp.json()["total_maintenance_cost"] == 200.0


def test_vehicle_maintenance_zero_cost_does_not_require_payment_target(client, db):
    make_user(db, email="fleet4@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet4@example.com")
    vehicle = _setup_vehicle(client, headers, "FL4")
    resp = client.post(
        "/api/vehicle-maintenances",
        json={"vehicle_id": vehicle["id"], "maintenance_date": "2026-05-02", "description": "Inspection gratuite", "cost": 0},
        headers=headers,
    )
    assert resp.status_code == 201


def test_maintenance_with_cost_requires_payment_target(client, db):
    make_user(db, email="fleet5@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet5@example.com")
    vehicle = _setup_vehicle(client, headers, "FL5")
    resp = client.post(
        "/api/vehicle-maintenances",
        json={"vehicle_id": vehicle["id"], "maintenance_date": "2026-05-02", "description": "Reparation", "cost": 300, "payment_method": "banque"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_cannot_complete_maintenance_twice(client, db):
    make_user(db, email="fleet6@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet6@example.com")
    vehicle = _setup_vehicle(client, headers, "FL6")
    maintenance = client.post(
        "/api/vehicle-maintenances",
        json={"vehicle_id": vehicle["id"], "maintenance_date": "2026-05-02", "description": "Freins", "cost": 0},
        headers=headers,
    ).json()
    client.post(f"/api/vehicle-maintenances/{maintenance['id']}/complete", headers=headers)
    resp = client.post(f"/api/vehicle-maintenances/{maintenance['id']}/complete", headers=headers)
    assert resp.status_code == 400


def test_vehicle_document_end_date_before_start_date_rejected(client, db):
    make_user(db, email="fleet7@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet7@example.com")
    vehicle = _setup_vehicle(client, headers, "FL7")
    resp = client.post(
        "/api/vehicle-documents",
        json={
            "vehicle_id": vehicle["id"],
            "document_type": "assurance",
            "start_date": "2026-06-01",
            "end_date": "2026-05-01",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_expiring_documents_endpoint_filters_by_window(client, db):
    make_user(db, email="fleet8@example.com", role_codes=FLEET_ROLES)
    headers = auth_headers(client, "fleet8@example.com")
    vehicle = _setup_vehicle(client, headers, "FL8")
    today = date.today()

    soon = client.post(
        "/api/vehicle-documents",
        json={
            "vehicle_id": vehicle["id"],
            "document_type": "assurance",
            "start_date": str(today - timedelta(days=300)),
            "end_date": str(today + timedelta(days=10)),
        },
        headers=headers,
    ).json()
    client.post(
        "/api/vehicle-documents",
        json={
            "vehicle_id": vehicle["id"],
            "document_type": "controle_technique",
            "start_date": str(today - timedelta(days=100)),
            "end_date": str(today + timedelta(days=200)),
        },
        headers=headers,
    )

    resp = client.get("/api/vehicle-documents/expiring?within_days=30", headers=headers)
    ids = [d["id"] for d in resp.json()]
    assert soon["id"] in ids
    assert len(ids) == 1


def test_stock_role_cannot_create_fuel_log_or_maintenance(client, db):
    make_user(db, email="stock_fleet1@example.com", role_codes=["stock"])
    headers = auth_headers(client, "stock_fleet1@example.com")
    resp = client.post(
        "/api/fuel-logs",
        json={"vehicle_id": 1, "log_date": "2026-05-01", "liters": 10, "unit_price": 10, "payment_method": "especes"},
        headers=headers,
    )
    assert resp.status_code == 403
    resp = client.post(
        "/api/vehicle-maintenances",
        json={"vehicle_id": 1, "maintenance_date": "2026-05-01", "description": "X", "cost": 0},
        headers=headers,
    )
    assert resp.status_code == 403
