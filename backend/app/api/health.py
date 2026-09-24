from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.core.db import get_engine

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> dict[str, str]:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "database": "down"},
        ) from exc
    return {"status": "ok", "database": "ok"}
