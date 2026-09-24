from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.auth import bootstrap_admin
from app.api.auth import router as auth_router
from app.api.contracts import router as contracts_router
from app.api.crm import router as crm_router
from app.api.documents import router as documents_router
from app.api.equipment import router as equipment_router
from app.api.health import router as health_router
from app.api.io_tables import router as io_router
from app.api.tasks import router as tasks_router
from app.api.works import router as works_router
from app.core.config import get_settings
from app.core.db import Base, get_engine, get_sessionmaker
from app.core.middleware import LoginRateLimitMiddleware, SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=get_engine())
    db = get_sessionmaker()()
    try:
        bootstrap_admin(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.3.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoginRateLimitMiddleware)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(crm_router)
    app.include_router(tasks_router)
    app.include_router(contracts_router)
    app.include_router(documents_router)
    app.include_router(works_router)
    app.include_router(equipment_router)
    app.include_router(io_router)
    return app


app = create_app()
