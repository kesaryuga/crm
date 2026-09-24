from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

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
from app.services.documents import find_placeholders_in_docx  # noqa: E402

ADMIN = {"email": "admin@kit-lab.by", "password": "ChangeMe!2026"}


def _mini_docx(text: str) -> bytes:
    """Минимальный DOCX с заданным текстом в document.xml."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


@pytest.fixture()
def db_session(tmp_path: Path):
    os.environ["STORAGE_LOCAL_PATH"] = str(tmp_path)
    from app.core.config import get_settings

    get_settings.cache_clear()
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
        get_settings.cache_clear()


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


def test_extract_placeholders() -> None:
    data = _mini_docx("Договор {{ contract.number }} от {{ contract.date }}")
    found = find_placeholders_in_docx(data)
    assert "contract.number" in found
    assert "contract.date" in found


def test_template_upload_and_generate_versions(client) -> None:
    data = _mini_docx("Договор № {{ contract.number }}")
    r = client.post(
        "/api/v1/templates",
        data={"code": "contract", "name": "Договор", "document_type": "contract"},
        files={
            "file": (
                "tpl.docx",
                data,
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            )
        },
    )
    assert r.status_code == 200, r.text
    tpl = r.json()
    assert tpl["placeholders"] == ["contract.number"]
    assert tpl["version"] == 1

    gen = client.post(
        "/api/v1/documents/generate",
        json={
            "entity_type": "contract",
            "entity_id": "c-1",
            "template_id": tpl["id"],
            "context": {"contract": {"number": "12"}},
        },
    )
    assert gen.status_code == 200, gen.text
    assert gen.json()["version_no"] == 1
    assert gen.json()["template_version"] == 1

    gen2 = client.post(
        "/api/v1/documents/generate",
        json={
            "entity_type": "contract",
            "entity_id": "c-1",
            "template_id": tpl["id"],
            "context": {"contract": {"number": "12"}},
        },
    )
    assert gen2.json()["version_no"] == 2

    listed = client.get("/api/v1/documents/contract/c-1").json()
    assert len(listed) == 2


def test_template_rejects_bad_extension(client) -> None:
    r = client.post(
        "/api/v1/templates",
        data={"code": "x", "name": "x", "document_type": "contract"},
        files={"file": ("evil.exe", b"MZ", "application/octet-stream")},
    )
    assert r.status_code == 400
