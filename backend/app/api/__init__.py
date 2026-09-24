from app.api.auth import router as auth_router
from app.api.contracts import router as contracts_router
from app.api.crm import router as crm_router
from app.api.documents import router as documents_router
from app.api.equipment import router as equipment_router
from app.api.health import router as health_router
from app.api.io_tables import router as io_router
from app.api.tasks import router as tasks_router
from app.api.works import router as works_router

__all__ = [
    "auth_router",
    "contracts_router",
    "crm_router",
    "documents_router",
    "equipment_router",
    "health_router",
    "io_router",
    "tasks_router",
    "works_router",
]
