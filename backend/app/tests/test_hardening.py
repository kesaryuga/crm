from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

from datetime import UTC, datetime  # noqa: E402

from app.api.auth import bootstrap_admin  # noqa: E402
from app.core.db import Base, get_db  # noqa: E402
from app.core.middleware import check_login_rate  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Contract, Counterparty  # noqa: E402

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


def test_unique_contract_number_blocks_duplicate(db_session) -> None:
    cp = Counterparty(full_name="X", unp="1")
    db_session.add(cp)
    db_session.flush()
    now = datetime.now(UTC)
    a = Contract(
        number="1",
        number_year=now.year,
        contract_date=now,
        counterparty_id=cp.id,
    )
    b = Contract(
        number="1",
        number_year=now.year,
        contract_date=now,
        counterparty_id=cp.id,
    )
    db_session.add(a)
    db_session.commit()
    db_session.add(b)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_api_number_conflict(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    payload = {
        "number": "77",
        "contract_date": datetime.now(UTC).isoformat(),
        "counterparty_id": cid,
    }
    assert client.post("/api/v1/contracts", json=payload).status_code == 200
    dup = client.post("/api/v1/contracts", json=payload)
    assert dup.status_code == 409
    assert dup.json()["detail"]["code"] == "CONTRACT_NUMBER_CONFLICT"


def test_login_rate_limit() -> None:
    for _ in range(10):
        assert check_login_rate("ip-test") is True
    assert check_login_rate("ip-test") is False
    assert check_login_rate("ip-other") is True


def test_security_headers(client) -> None:
    r = client.get("/health/live")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"


def test_upload_rejects_bad_ext(client) -> None:
    r = client.post(
        "/api/v1/templates",
        data={"code": "x", "name": "x", "document_type": "contract"},
        files={"file": ("virus.bat", b"@echo off", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_work_number_conflict(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    payload = {
        "number": "5",
        "work_date": datetime.now(UTC).isoformat(),
        "counterparty_id": cid,
    }
    assert client.post("/api/v1/works", json=payload).status_code == 200
    assert client.post("/api/v1/works", json=payload).status_code == 409
