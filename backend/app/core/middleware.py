from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

_LOGIN_LIMIT = 30
_LOGIN_WINDOW = 60.0
_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def reset_login_rate() -> None:
    with _lock:
        _hits.clear()


def check_login_rate(key: str, enabled: bool = True) -> bool:
    if not enabled:
        return True
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and q[0] < now - _LOGIN_WINDOW:
            q.popleft()
        if len(q) >= _LOGIN_LIMIT:
            return False
        q.append(now)
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.endswith("/auth/login") and request.method == "POST":
            if get_settings().login_rate_limit_enabled:
                client = request.client.host if request.client else "unknown"
                if not check_login_rate(client):
                    return Response(
                        content=(
                            '{"code":"RATE_LIMITED",'
                            '"message":"Слишком много попыток входа"}'
                        ),
                        status_code=429,
                        media_type="application/json",
                    )
        return await call_next(request)
