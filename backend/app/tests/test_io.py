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
CSV = (
    "full_name,short_name,unp,phone,email\n"
    "ООО «СтройСервис»,СтройСервис,190123456,+375291112233,info@stroy.by\n"
    "ООО «ТехЭкспертиза\",ТЭ,191987654,,office@teh.by\n"
)


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


def test_import_preview_and_commit(client) -> None:
    preview = client.post(
        "/api/v1/import/counterparties/preview",
        files={"file": ("cp.csv", CSV.encode("utf-8"), "text/csv")},
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["total"] == 2
    assert body["rows"][0]["full_name"] == "ООО «СтройСервис»"

    commit = client.post(
        "/api/v1/import/counterparties",
        files={"file": ("cp.csv", CSV.encode("utf-8"), "text/csv")},
    )
    assert commit.status_code == 200
    assert commit.json()["created"] == 2

    again = client.post(
        "/api/v1/import/counterparties",
        files={"file": ("cp.csv", CSV.encode("utf-8"), "text/csv")},
    )
    assert again.json()["created"] == 0
    assert again.json()["skipped"] == 2


def test_export_csv(client) -> None:
    client.post(
        "/api/v1/import/counterparties",
        files={"file": ("cp.csv", CSV.encode("utf-8"), "text/csv")},
    )
    r = client.get("/api/v1/export/counterparties.csv")
    assert r.status_code == 200
    assert "full_name" in r.text
    assert "СтройСервис" in r.text

    t = client.get("/api/v1/export/tasks.csv")
    assert t.status_code == 200
    assert "title" in t.text

    c = client.get("/api/v1/export/contracts.csv")
    assert c.status_code == 200
    assert "number" in c.text
