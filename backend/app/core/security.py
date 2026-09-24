from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def _sign(value: str) -> str:
    key = get_settings().secret_key.encode()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:32]


def create_session_token(user_id: str) -> str:
    ts = str(int(time.time()))
    return f"{user_id}.{ts}.{_sign(f'{user_id}.{ts}')}"


def parse_session_token(token: str) -> str | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    user_id, ts, sig = parts
    if not hmac.compare_digest(_sign(f"{user_id}.{ts}"), sig):
        return None
    return user_id


def audit_payload(old: Any = None, new: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if old is not None:
        payload["old"] = old
    if new is not None:
        payload["new"] = new
    return payload
