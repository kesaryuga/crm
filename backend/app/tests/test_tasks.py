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


def test_task_lifecycle(client, db_session) -> None:
    me = client.get("/api/v1/auth/me").json()
    payload = {
        "title": "Испытания склада, Минская 12 — 2 места",
        "description": "Освещённость, заземление, температура",
        "task_type": "test",
        "assignee_user_id": me["id"],
        "priority": "high",
        "due_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }
    r = client.post("/api/v1/tasks", json=payload)
    assert r.status_code == 200, r.text
    tid = r.json()["id"]
    assert r.json()["status"] == "new"

    assert client.get(f"/api/v1/tasks/{tid}").json()["title"].startswith("Испытания")

    patched = client.patch(f"/api/v1/tasks/{tid}", json={**payload, "status": "in_progress"})
    assert patched.json()["status"] == "in_progress"

    done = client.post(f"/api/v1/tasks/{tid}/complete", json={"comment": "Готово"})
    assert done.json()["status"] == "completed"
    assert done.json()["is_overdue"] is False
    assert done.json()["completed_at"] is not None


def test_overdue_flag(client, db_session) -> None:
    me = client.get("/api/v1/auth/me").json()
    payload = {
        "title": "Проверить оплату по договору №8",
        "assignee_user_id": me["id"],
        "due_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
    }
    r = client.post("/api/v1/tasks", json=payload)
    assert r.json()["is_overdue"] is True

    overdue = client.get("/api/v1/tasks", params={"overdue": True}).json()
    assert overdue[0]["title"] == payload["title"]


def test_task_comment_and_dashboard(client, db_session) -> None:
    me = client.get("/api/v1/auth/me").json()
    tid = client.post(
        "/api/v1/tasks",
        json={"title": "Позвонить по договору №12", "assignee_user_id": me["id"]},
    ).json()["id"]

    r = client.post(
        f"/api/v1/tasks/{tid}/comments",
        params={"body": "Контакт Петров, звонить после 14:00", "is_executor_note": True},
    )
    assert r.status_code == 200

    comments = client.get("/api/v1/comments", params={"entity_type": "task", "entity_id": tid})
    assert comments.json()[0]["is_executor_note"] is True

    dash = client.get("/api/v1/dashboard").json()
    assert dash["my_open_tasks"] >= 1
    assert "overdue" in dash
