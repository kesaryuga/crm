from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import (
    Equipment,
    EquipmentVerification,
    Protocol,
    ProtocolEquipment,
    User,
)
from app.services import write_audit

router = APIRouter(prefix="/api/v1", tags=["equipment"])

WARN_DAYS = 30


class EquipmentIn(BaseModel):
    equipment_type: str = ""
    name: str = Field(min_length=1)
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    inventory_number: str = ""
    measurement_range: str = ""
    units: str = ""
    status: str = "active"
    notes: str = ""


class EquipmentOut(EquipmentIn):
    id: str
    verification_status: str = "unknown"
    valid_until: str | None = None


class VerificationIn(BaseModel):
    verification_date: datetime
    valid_until: datetime
    certificate_number: str = ""
    verifier: str = ""
    notes: str = ""


class VerificationOut(VerificationIn):
    id: str
    equipment_id: str
    status: str = "unknown"


class AttachIn(BaseModel):
    equipment_id: str
    verification_id: str
    allow_expired: bool = False


def _verify_status(valid_until: datetime, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    vu = valid_until if valid_until.tzinfo else valid_until.replace(tzinfo=UTC)
    if vu < now:
        return "expired"
    if vu < now + timedelta(days=WARN_DAYS):
        return "expiring"
    return "ok"


def _eq_out(e: Equipment, latest: EquipmentVerification | None) -> EquipmentOut:
    status = "unknown"
    valid_until = None
    if latest:
        status = _verify_status(latest.valid_until)
        valid_until = latest.valid_until.isoformat()
    return EquipmentOut(
        id=e.id,
        equipment_type=e.equipment_type,
        name=e.name,
        manufacturer=e.manufacturer,
        model=e.model,
        serial_number=e.serial_number,
        inventory_number=e.inventory_number,
        measurement_range=e.measurement_range,
        units=e.units,
        status=e.status,
        notes=e.notes,
        verification_status=status,
        valid_until=valid_until,
    )


def _ver_out(v: EquipmentVerification) -> VerificationOut:
    return VerificationOut(
        id=v.id,
        equipment_id=v.equipment_id,
        verification_date=v.verification_date,
        valid_until=v.valid_until,
        certificate_number=v.certificate_number,
        verifier=v.verifier,
        notes=v.notes,
        status=_verify_status(v.valid_until),
    )


def _latest_verification(db: Session, equipment_id: str) -> EquipmentVerification | None:
    return db.scalars(
        select(EquipmentVerification)
        .where(EquipmentVerification.equipment_id == equipment_id)
        .order_by(EquipmentVerification.valid_until.desc())
    ).first()


@router.get("/equipment", response_model=list[EquipmentOut])
def list_equipment(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[EquipmentOut]:
    rows = db.scalars(
        select(Equipment).where(Equipment.deleted_at.is_(None)).order_by(Equipment.name)
    ).all()
    return [_eq_out(e, _latest_verification(db, e.id)) for e in rows]


@router.post("/equipment", response_model=EquipmentOut)
def create_equipment(
    payload: EquipmentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EquipmentOut:
    row = Equipment(**payload.model_dump())
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="equipment",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _eq_out(row, None)


@router.patch("/equipment/{eid}", response_model=EquipmentOut)
def update_equipment(
    eid: str,
    payload: EquipmentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EquipmentOut:
    row = db.get(Equipment, eid)
    if not row or row.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Прибор не найден"},
        )
    for key, val in payload.model_dump().items():
        setattr(row, key, val)
    write_audit(db, actor_user_id=user.id, action="update", entity_type="equipment", entity_id=eid)
    db.commit()
    db.refresh(row)
    return _eq_out(row, _latest_verification(db, eid))


@router.post("/equipment/{eid}/verifications", response_model=VerificationOut)
def add_verification(
    eid: str,
    payload: VerificationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VerificationOut:
    row = db.get(Equipment, eid)
    if not row or row.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Прибор не найден"},
        )
    ver = EquipmentVerification(equipment_id=eid, **payload.model_dump())
    db.add(ver)
    write_audit(
        db,
        actor_user_id=user.id,
        action="verify",
        entity_type="equipment",
        entity_id=eid,
    )
    db.commit()
    db.refresh(ver)
    return _ver_out(ver)


@router.get("/equipment/{eid}/verifications", response_model=list[VerificationOut])
def list_verifications(
    eid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[VerificationOut]:
    rows = db.scalars(
        select(EquipmentVerification)
        .where(EquipmentVerification.equipment_id == eid)
        .order_by(EquipmentVerification.valid_until.desc())
    ).all()
    return [_ver_out(v) for v in rows]


@router.post("/protocols/{pid}/equipment")
def attach_equipment(
    pid: str,
    payload: AttachIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    proto = db.get(Protocol, pid)
    if not proto or proto.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Протокол не найден"},
        )
    equip = db.get(Equipment, payload.equipment_id)
    ver = db.get(EquipmentVerification, payload.verification_id)
    if not equip or not ver or ver.equipment_id != equip.id:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_LINK", "message": "Поверка не относится к прибору"},
        )

    status = _verify_status(ver.valid_until)
    proto_date = proto.protocol_date
    vu = ver.valid_until
    if vu.tzinfo is None and proto_date.tzinfo is not None:
        vu = vu.replace(tzinfo=UTC)
    if status == "expired" and not payload.allow_expired:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VERIFICATION_EXPIRED",
                "message": "Поверка просрочена",
                "warning": True,
            },
        )
    if vu < proto_date:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VERIFICATION_BEFORE_PROTOCOL",
                "message": "Срок поверки раньше даты протокола",
                "warning": True,
            },
        )

    db.add(
        ProtocolEquipment(
            protocol_id=pid,
            equipment_id=payload.equipment_id,
            verification_id=payload.verification_id,
        )
    )
    write_audit(
        db,
        actor_user_id=user.id,
        action="attach_equipment",
        entity_type="protocol",
        entity_id=pid,
    )
    db.commit()
    return {"status": "attached", "verification_status": status}
