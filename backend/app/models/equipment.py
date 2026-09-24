from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    equipment_type: Mapped[str] = mapped_column(String(120), default="")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(255), default="")
    model: Mapped[str] = mapped_column(String(255), default="")
    serial_number: Mapped[str] = mapped_column(String(120), default="", index=True)
    inventory_number: Mapped[str] = mapped_column(String(120), default="")
    measurement_range: Mapped[str] = mapped_column(String(255), default="")
    units: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EquipmentVerification(Base):
    __tablename__ = "equipment_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    equipment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("equipment.id", ondelete="CASCADE"), index=True
    )
    verification_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    certificate_number: Mapped[str] = mapped_column(String(120), default="")
    verifier: Mapped[str] = mapped_column(String(255), default="")
    file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProtocolEquipment(Base):
    __tablename__ = "protocol_equipment"
    __table_args__ = (
        UniqueConstraint(
            "protocol_id",
            "equipment_id",
            "verification_id",
            name="uq_protocol_equip_ver",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    protocol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("protocols.id", ondelete="CASCADE"), index=True
    )
    equipment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("equipment.id", ondelete="RESTRICT")
    )
    verification_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("equipment_verifications.id", ondelete="RESTRICT"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
