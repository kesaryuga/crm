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
from app.main import app  # noqa: E402

ADMIN = {"email": "admin@kit-lab.by", "password": "ChangeMe!2026"}
CP = {
    "full_name": "ООО «СтройСервис»",
    "unp": "190123456",
    "phone": "+375 29 111-22-33",
}


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
        bootstrap_admin(db_session)
        c.post("/api/v1/auth/login", json=ADMIN)
        yield c
    app.dependency_overrides.clear()


def test_counterparty_crud_and_soft_delete(client) -> None:
    r = client.post("/api/v1/counterparties", json=CP)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]

    listed = client.get("/api/v1/counterparties").json()
    assert listed[0]["full_name"] == CP["full_name"]
    assert client.get(f"/api/v1/counterparties/{cid}").json()["unp"] == "190123456"

    upd = dict(CP, status="inactive", notes="на паузе")
    assert client.patch(f"/api/v1/counterparties/{cid}", json=upd).json()["status"] == "inactive"

    assert client.delete(f"/api/v1/counterparties/{cid}").json()["status"] == "archived"
    assert client.get(f"/api/v1/counterparties/{cid}").status_code == 404
    assert client.get("/api/v1/counterparties").json() == []


def test_contacts_objects_comments(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]

    contact = client.post(
        "/api/v1/contacts",
        json={
            "counterparty_id": cid,
            "full_name": "Петров И.И.",
            "phone": "+375 29 111",
            "is_primary": True,
        },
    )
    assert contact.status_code == 200
    contacts = client.get(f"/api/v1/counterparties/{cid}/contacts").json()
    assert contacts[0]["full_name"] == "Петров И.И."

    obj = client.post(
        "/api/v1/objects",
        json={
            "counterparty_id": cid,
            "name": "Склад, Минская 12",
            "address": "г. Минск, ул. Минская, 12",
        },
    )
    assert obj.status_code == 200
    objs = client.get(f"/api/v1/counterparties/{cid}/objects").json()
    assert objs[0]["name"] == "Склад, Минская 12"

    cm = client.post(
        "/api/v1/comments",
        json={
            "entity_type": "counterparty",
            "entity_id": cid,
            "body": "Пришёл с сайта kit-lab.by",
        },
    )
    assert cm.status_code == 200
    assert cm.json()["is_executor_note"] is False

    note = client.post(
        "/api/v1/comments",
        json={
            "entity_type": "counterparty",
            "entity_id": cid,
            "body": "Принял заявку",
            "is_executor_note": True,
        },
    )
    assert note.json()["is_executor_note"] is True

    hist = client.get(f"/api/v1/counterparties/{cid}/history").json()
    assert len(hist) == 2


def test_search(client) -> None:
    client.post("/api/v1/counterparties", json=CP)
    r = client.get("/api/v1/search", params={"q": "Строй"})
    assert r.status_code == 200
    assert r.json()["counterparties"][0]["title"] == CP["full_name"]


def test_requires_auth() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = factory()
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as c:
        assert c.get("/api/v1/counterparties").status_code == 401
    app.dependency_overrides.clear()
    session.close()
    engine.dispose()
