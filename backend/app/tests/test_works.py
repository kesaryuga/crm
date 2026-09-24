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
from app.services import FormulaError, eval_formula  # noqa: E402

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


def test_formula_safe_math() -> None:
    got = eval_formula(
        "(measured - design) / design * 100",
        {"measured": 110, "design": 100},
    )
    assert got == Decimal("10.00")
    assert eval_formula("min(a, b)", {"a": 3, "b": 5}) == Decimal("3.00")
    assert eval_formula("abs(x)", {"x": -4}) == Decimal("4.00")


def test_formula_rejects_unsafe() -> None:
    with pytest.raises(FormulaError):
        eval_formula("__import__('os')", {})
    with pytest.raises(FormulaError):
        eval_formula("open('/etc/passwd')", {})
    with pytest.raises(FormulaError):
        eval_formula("x / 0", {"x": 1})
    with pytest.raises(FormulaError):
        eval_formula("unknown + 1", {})


def test_work_and_protocol_flow(client) -> None:
    cid = client.post("/api/v1/counterparties", json=CP).json()["id"]
    work = client.post(
        "/api/v1/works",
        json={
            "number": "15",
            "work_date": datetime.now(UTC).isoformat(),
            "counterparty_id": cid,
            "status": "in_progress",
        },
    )
    assert work.status_code == 200, work.text
    assert work.json()["number"] == "15"

    dup = client.post(
        "/api/v1/works",
        json={
            "number": "15",
            "work_date": datetime.now(UTC).isoformat(),
            "counterparty_id": cid,
        },
    )
    assert dup.status_code == 409

    ptype = client.post(
        "/api/v1/protocol-types",
        json={
            "code": "elec",
            "name": "Электролаборатория",
            "calculation_schema_json": (
                '{"row_formulas": {"delta": "(measured - design) / design * 100"}}'
            ),
        },
    ).json()

    proto = client.post(
        "/api/v1/protocols",
        json={
            "number": "7",
            "protocol_date": datetime.now(UTC).isoformat(),
            "protocol_type_id": ptype["id"],
            "work_id": work.json()["id"],
            "counterparty_id": cid,
        },
    ).json()
    pid = proto["id"]

    rows = client.put(
        f"/api/v1/protocols/{pid}/rows",
        json=[
            {"section_code": "main", "row_no": 1, "values": {"measured": 110, "design": 100}},
            {"section_code": "main", "row_no": 2, "values": {"measured": 50, "design": 100}},
        ],
    )
    assert rows.status_code == 200
    assert len(rows.json()["rows"]) == 2

    rec = client.post(f"/api/v1/protocols/{pid}/recalculate")
    assert rec.status_code == 200, rec.text
    calc = rec.json()["rows"][0]["calculated"]
    assert calc["delta"] == "10.00"
    calc2 = rec.json()["rows"][1]["calculated"]
    assert calc2["delta"] == "-50.00"
