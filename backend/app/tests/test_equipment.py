from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

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
CP = {"full_name": "ООО «СтройСервис»", "unp": "190123456"}


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


def test_equipment_and_verification_status(client) -> None:
    now = datetime.now(UTC)
    eq = client.post(
        "/api/v1/equipment",
        json={"name": "Мультиметр Fluke 87V", "serial_number": "FL-90211"},
    ).json()
    assert eq["verification_status"] == "unknown"

    ver = client.post(
        f"/api/v1/equipment/{eq['id']}/verifications",
        json={
            "verification_date": (now - timedelta(days=30)).isoformat(),
            "valid_until": (now - timedelta(days=1)).isoformat(),
            "certificate_number": "ПВ-1",
        },
    )
    assert ver.status_code == 200
    assert ver.json()["status"] == "expired"

    eq2 = client.get("/api/v1/equipment").json()[0]
    assert eq2["verification_status"] == "expired"

    ver2 = client.post(
        f"/api/v1/equipment/{eq['id']}/verifications",
        json={
            "verification_date": now.isoformat(),
            "valid_until": (now + timedelta(days=10)).isoformat(),
            "certificate_number": "ПВ-2",
        },
    ).json()
    assert ver2["status"] == "expiring"

    eq3 = client.get("/api/v1/equipment").json()[0]
    assert eq3["verification_status"] == "expiring"
    assert eq3["valid_until"] is not None


def test_attach_equipment_to_protocol(client) -> None:
    now = datetime.now(UTC)
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    ptype = client.post(
        "/api/v1/protocol-types",
        json={"code": "elec", "name": "Электро"},
    ).json()
    proto = client.post(
        "/api/v1/protocols",
        json={
            "number": "1",
            "protocol_date": now.isoformat(),
            "protocol_type_id": ptype["id"],
            "counterparty_id": cid,
        },
    ).json()
    eq = client.post(
        "/api/v1/equipment",
        json={"name": "Тепловизор Testo 872", "serial_number": "TS-33100"},
    ).json()
    ok_ver = client.post(
        f"/api/v1/equipment/{eq['id']}/verifications",
        json={
            "verification_date": now.isoformat(),
            "valid_until": (now + timedelta(days=200)).isoformat(),
        },
    ).json()
    bad_ver = client.post(
        f"/api/v1/equipment/{eq['id']}/verifications",
        json={
            "verification_date": (now - timedelta(days=400)).isoformat(),
            "valid_until": (now - timedelta(days=100)).isoformat(),
        },
    ).json()

    bad = client.post(
        f"/api/v1/protocols/{proto['id']}/equipment",
        json={
            "equipment_id": eq["id"],
            "verification_id": bad_ver["id"],
            "allow_expired": False,
        },
    )
    assert bad.status_code == 400
    assert bad.json()["detail"]["code"] == "VERIFICATION_EXPIRED"

    ok = client.post(
        f"/api/v1/protocols/{proto['id']}/equipment",
        json={
            "equipment_id": eq["id"],
            "verification_id": ok_ver["id"],
            "allow_expired": False,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "attached"
    assert ok.json()["verification_status"] == "ok"
