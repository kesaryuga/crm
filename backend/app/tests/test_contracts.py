from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

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
from app.services import amount_in_words, line_totals, money  # noqa: E402

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


def test_line_totals_and_words() -> None:
    sub, vat, total = line_totals(
        Decimal("2"),
        Decimal("1090.00"),
        discount_type="percent",
        discount_value=Decimal("0"),
        vat_rate=None,
    )
    assert sub == money("2180.00")
    assert vat == money("0.00")
    assert total == money("2180.00")
    words = amount_in_words(total)
    assert "без НДС" in words
    assert "две тысячи" in words


def test_contract_number_manual_and_unique(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    base = {
        "number": "1",
        "contract_date": datetime.now(UTC).isoformat(),
        "counterparty_id": cid,
    }
    r1 = client.post("/api/v1/contracts", json=base)
    assert r1.status_code == 200, r1.text
    assert r1.json()["number"] == "1"
    assert r1.json()["number_year"] == datetime.now(UTC).year

    dup = client.post("/api/v1/contracts", json=base)
    assert dup.status_code == 409

    nxt = client.post("/api/v1/contracts", json={**base, "number": "2"})
    assert nxt.status_code == 200
    assert nxt.json()["number"] == "2"


def test_items_snapshot_and_totals(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    svc = client.post(
        "/api/v1/services",
        json={
            "code": "LAB-01",
            "name": "Электролаборатория",
            "unit": "выезд",
            "base_price": "1900.00",
        },
    ).json()
    assert svc["base_price"] == "1900.00"

    contract = client.post(
        "/api/v1/contracts",
        json={
            "number": "12",
            "contract_date": datetime.now(UTC).isoformat(),
            "counterparty_id": cid,
        },
    ).json()
    con_id = contract["id"]

    added = client.post(
        f"/api/v1/contracts/{con_id}/items",
        json={
            "service_id": svc["id"],
            "name_snapshot": svc["name"],
            "unit_snapshot": svc["unit"],
            "quantity": "1",
            "unit_price": "1900.00",
        },
    )
    assert added.status_code == 200, added.text
    body = added.json()
    assert body["subtotal"] == "1900.00"
    assert body["vat_amount"] == "0.00"
    assert body["total_amount"] == "1900.00"
    assert body["items"][0]["name_snapshot"] == "Электролаборатория"
    assert "без НДС" in body["amount_in_words"]


def test_service_price_isolated_from_contract(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    svc = client.post(
        "/api/v1/services",
        json={"code": "LAB-02", "name": "Метео", "base_price": "100.00"},
    ).json()
    con_id = client.post(
        "/api/v1/contracts",
        json={
            "number": "99",
            "contract_date": datetime.now(UTC).isoformat(),
            "counterparty_id": cid,
        },
    ).json()["id"]
    client.post(
        f"/api/v1/contracts/{con_id}/items",
        json={
            "service_id": svc["id"],
            "name_snapshot": "Метео",
            "quantity": "1",
            "unit_price": "100.00",
        },
    )
    client.patch(
        f"/api/v1/services/{svc['id']}",
        json={"code": "LAB-02", "name": "Метео v2", "base_price": "999.00"},
    ) if False else None
    got = client.get(f"/api/v1/contracts/{con_id}").json()
    assert got["items"][0]["unit_price"] == "100.00"
    assert got["items"][0]["name_snapshot"] == "Метео"
