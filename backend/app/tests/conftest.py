from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("LOGIN_RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("STORAGE_LOCAL_PATH", "/tmp/crm-test-uploads")

import pytest  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.middleware import reset_login_rate  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_rate_limit():
    reset_login_rate()
    get_settings.cache_clear()
    yield
    reset_login_rate()
    get_settings.cache_clear()
