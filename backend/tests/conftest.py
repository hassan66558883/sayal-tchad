import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://seyal:seyal_dev_password@localhost:5432/seyal_test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import Role, User
from app.services.audit import register_audit_listeners
from app.services.seed import seed

engine = create_engine(settings.database_url, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    register_audit_listeners()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(db, *, name="Test User", email="test@example.com", password="pass1234", role_codes=None, is_superuser=False):
    roles = db.query(Role).filter(Role.code.in_(role_codes or [])).all()
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        roles=roles,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(client, email, password="pass1234"):
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
