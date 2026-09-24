from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class IdempotencyKey(Base):
    """Защита от двойного submit: повторный POST с тем же ключом не создаёт дубль."""

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    scope: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(36), default="")


def new_key() -> str:
    return uuid.uuid4().hex
