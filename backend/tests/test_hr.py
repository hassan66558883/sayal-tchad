from tests.conftest import auth_headers, make_user

RH_ROLES = ["rh", "achats", "ventes"]


def test_create_employee_requires_rh_role(client, db):
    make_user(db, email="hr1@example.com", role_codes=["ventes"])
    headers = auth_headers(client, "hr1@example.com")
    resp = client.post(
        "/api/employees",
        json={"name": "Employe X", "position": "Vendeur", "hire_date": "2026-01-01", "base_salary": 1000},
        headers=headers,
    )
    assert resp.status_code == 403


def test_leave_request_own_employee_can_create_and_see_own(client, db):
    rh_user = make_user(db, email="hr2@example.com", role_codes=RH_ROLES)
    rh_headers = auth_headers(client, "hr2@example.com")
    employee_user = make_user(db, email="employee2@example.com", role_codes=[])
    employee = client.post(
        "/api/employees",
        json={
            "name": "Employe Y",
            "user_id": employee_user.id,
            "position": "Chauffeur",
            "hire_date": "2026-01-01",
            "base_salary": 1500,
        },
        headers=rh_headers,
    ).json()

    other_employee = client.post(
        "/api/employees",
        json={"name": "Employe Z", "position": "Comptable", "hire_date": "2026-01-01", "base_salary": 2000},
        headers=rh_headers,
    ).json()

    employee_headers = auth_headers(client, "employee2@example.com")
    resp = client.post(
        "/api/leave-requests",
        json={"employee_id": employee["id"], "start_date": "2026-08-01", "end_date": "2026-08-05"},
        headers=employee_headers,
    )
    assert resp.status_code == 201, resp.text

    # cannot request leave for someone else
    resp2 = client.post(
        "/api/leave-requests",
        json={"employee_id": other_employee["id"], "start_date": "2026-08-01", "end_date": "2026-08-05"},
        headers=employee_headers,
    )
    assert resp2.status_code == 403

    seen = client.get("/api/leave-requests", headers=employee_headers).json()
    assert {r["employee_id"] for r in seen} == {employee["id"]}


def test_rh_can_approve_and_reject_leave_requests(client, db):
    rh_headers = auth_headers(client, make_user(db, email="hr3@example.com", role_codes=RH_ROLES).email)
    employee = client.post(
        "/api/employees",
        json={"name": "Employe A3", "position": "Caissier", "hire_date": "2026-01-01", "base_salary": 1200},
        headers=rh_headers,
    ).json()
    req1 = client.post(
        "/api/leave-requests",
        json={"employee_id": employee["id"], "start_date": "2026-08-01", "end_date": "2026-08-03"},
        headers=rh_headers,
    ).json()
    req2 = client.post(
        "/api/leave-requests",
        json={"employee_id": employee["id"], "start_date": "2026-09-01", "end_date": "2026-09-03"},
        headers=rh_headers,
    ).json()

    approved = client.post(f"/api/leave-requests/{req1['id']}/approve", headers=rh_headers)
    assert approved.status_code == 200
    assert approved.json()["state"] == "approuvee"

    rejected = client.post(f"/api/leave-requests/{req2['id']}/reject", headers=rh_headers)
    assert rejected.status_code == 200
    assert rejected.json()["state"] == "refusee"

    resp = client.post(f"/api/leave-requests/{req1['id']}/approve", headers=rh_headers)
    assert resp.status_code == 400  # already approved


def test_leave_request_end_before_start_rejected(client, db):
    rh_headers = auth_headers(client, make_user(db, email="hr4@example.com", role_codes=RH_ROLES).email)
    employee = client.post(
        "/api/employees",
        json={"name": "Employe A4", "position": "Magasinier", "hire_date": "2026-01-01", "base_salary": 900},
        headers=rh_headers,
    ).json()
    resp = client.post(
        "/api/leave-requests",
        json={"employee_id": employee["id"], "start_date": "2026-08-10", "end_date": "2026-08-01"},
        headers=rh_headers,
    )
    assert resp.status_code == 422


def test_payslip_net_pay_and_requires_payment_target_to_validate(client, db):
    rh_headers = auth_headers(client, make_user(db, email="hr5@example.com", role_codes=RH_ROLES).email)
    employee = client.post(
        "/api/employees",
        json={"name": "Employe A5", "position": "RH", "hire_date": "2026-01-01", "base_salary": 3000},
        headers=rh_headers,
    ).json()
    payslip = client.post(
        "/api/payslips",
        json={
            "employee_id": employee["id"],
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
            "base_salary": 3000,
            "bonuses": 200,
            "deductions": 150,
            "payment_method": "especes",
        },
        headers=rh_headers,
    ).json()
    assert payslip["net_pay"] == 3050.0
    assert payslip["reference"].startswith("BUL")

    resp = client.post(f"/api/payslips/{payslip['id']}/validate", headers=rh_headers)
    assert resp.status_code == 400  # no cash session provided


def test_payslip_validation_reduces_cash_session_balance(client, db):
    rh_headers = auth_headers(client, make_user(db, email="hr6@example.com", role_codes=RH_ROLES + ["comptable", "caissier"]).email)
    employee = client.post(
        "/api/employees",
        json={"name": "Employe A6", "position": "Vendeur", "hire_date": "2026-01-01", "base_salary": 1000},
        headers=rh_headers,
    ).json()
    register = client.post("/api/cash-registers", json={"name": "Caisse HR6", "code": "CR-HR6"}, headers=rh_headers).json()
    session = client.post(
        "/api/cash-sessions", json={"register_id": register["id"], "opening_balance": 5000}, headers=rh_headers
    ).json()

    payslip = client.post(
        "/api/payslips",
        json={
            "employee_id": employee["id"],
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
            "base_salary": 1000,
            "payment_method": "especes",
            "cash_session_id": session["id"],
        },
        headers=rh_headers,
    ).json()
    resp = client.post(f"/api/payslips/{payslip['id']}/validate", headers=rh_headers)
    assert resp.status_code == 200
    assert resp.json()["state"] == "validated"

    sessions = client.get("/api/cash-sessions", headers=rh_headers).json()
    this_session = next(s for s in sessions if s["id"] == session["id"])
    assert this_session["computed_balance"] == 4000.0


def test_hr_summary_report(client, db):
    rh_headers = auth_headers(client, make_user(db, email="hr7@example.com", role_codes=RH_ROLES).email)
    client.post(
        "/api/employees",
        json={"name": "Employe A7", "position": "Vendeur", "hire_date": "2026-01-01", "base_salary": 1000},
        headers=rh_headers,
    )
    resp = client.get("/api/reports/hr-summary?period_start=2026-01-01&period_end=2026-12-31", headers=rh_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_employee_count"] >= 1


def test_sales_summary_report_requires_role(client, db):
    make_user(db, email="hr8@example.com", role_codes=["stock"])
    headers = auth_headers(client, "hr8@example.com")
    resp = client.get("/api/reports/sales-summary?period_start=2026-01-01&period_end=2026-12-31", headers=headers)
    assert resp.status_code == 403
