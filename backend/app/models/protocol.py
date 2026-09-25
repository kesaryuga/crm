from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Work(Base):
    __tablename__ = "works"
    __table_args__ = (UniqueConstraint("number", "number_year", name="uq_work_number_year"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    number_year: Mapped[int | None] = mapped_column(nullable=True)
    work_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    counterparty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("counterparties.id", ondelete="RESTRICT"), index=True
    )
    object_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("objects.id", ondelete="SET NULL"), nullable=True
    )
    contract_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    service_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )
    assignee_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="planned", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    # карточка испытания
    test_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    address: Mapped[str] = mapped_column(String(500), default="")
    parameters_count: Mapped[int] = mapped_column(Integer, default=0)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    method: Mapped[str] = mapped_column(String(255), default="")
    contact_person: Mapped[str] = mapped_column(String(255), default="")
    contact_phone: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProtocolType(Base):
    __tablename__ = "protocol_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    schema_json: Mapped[str] = mapped_column(Text, default="{}")
    calculation_schema_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Protocol(Base):
    __tablename__ = "protocols"
    __table_args__ = (
        UniqueConstraint("number", "number_year", name="uq_protocol_number_year"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    number_year: Mapped[int | None] = mapped_column(nullable=True)
    protocol_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    protocol_type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("protocol_types.id", ondelete="RESTRICT")
    )
    work_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("works.id", ondelete="SET NULL"), nullable=True
    )
    counterparty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("counterparties.id", ondelete="RESTRICT")
    )
    object_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("objects.id", ondelete="SET NULL"), nullable=True
    )
    contract_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    responsible_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    form_data_json: Mapped[str] = mapped_column(Text, default="{}")
    calculated_data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProtocolRow(Base):
    __tablename__ = "protocol_rows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    protocol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("protocols.id", ondelete="CASCADE"), index=True
    )
    section_code: Mapped[str] = mapped_column(String(64), default="main")
    row_no: Mapped[int] = mapped_column(Integer, default=1)
    values_json: Mapped[str] = mapped_column(Text, default="{}")
    calculated_json: Mapped[str] = mapped_column(Text, default="{}")
