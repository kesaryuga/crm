from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.api.auth import bootstrap_admin  # noqa: E402
from app.core.db import Base, get_db  # noqa: E402
from app.core.security import hash_password, verify_password  # noqa: E402
from app.main import app  # noqa: E402

ADMIN = {"email": "admin@kit-lab.by", "password": "ChangeMe!2026"}


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_password_hash_roundtrip() -> None:
    h = hash_password("Secret!123")
    assert verify_password(h, "Secret!123")
    assert not verify_password(h, "wrong")


def test_login_success_and_me(client, db_session) -> None:
    bootstrap_admin(db_session)
    r = client.post("/api/v1/auth/login", json=ADMIN)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == ADMIN["email"]
    assert body["role"] == "admin"
    assert "admin.all" in body["permissions"]

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN["email"]


def test_login_fail(client, db_session) -> None:
    bootstrap_admin(db_session)
    r = client.post("/api/v1/auth/login", json={"email": ADMIN["email"], "password": "bad"})
    assert r.status_code == 401


def test_inactive_user_blocked(client, db_session) -> None:
    user = bootstrap_admin(db_session)
    user.is_active = False
    db_session.commit()
    r = client.post("/api/v1/auth/login", json=ADMIN)
    assert r.status_code == 403


def test_me_without_session(client) -> None:
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_logout(client, db_session) -> None:
    bootstrap_admin(db_session)
    client.post("/api/v1/auth/login", json=ADMIN)
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
