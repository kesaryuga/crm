from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import Protocol, ProtocolRow, ProtocolType, User, Work
from app.services import FormulaError, eval_formula, write_audit

router = APIRouter(prefix="/api/v1", tags=["works"])


class WorkIn(BaseModel):
    number: str = Field(min_length=1)
    number_year: int | None = None
    work_date: datetime
    counterparty_id: str
    object_id: str | None = None
    contract_id: str | None = None
    service_id: str | None = None
    assignee_user_id: str | None = None
    status: str = "planned"
    notes: str = ""
    test_type: str = ""
    address: str = ""
    parameters_count: int = 0
    sample_count: int = 0
    method: str = ""
    contact_person: str = ""
    contact_phone: str = ""


class WorkOut(BaseModel):
    id: str
    number: str
    number_year: int | None
    work_date: datetime
    counterparty_id: str
    object_id: str | None
    contract_id: str | None
    service_id: str | None
    assignee_user_id: str | None
    status: str
    notes: str
    test_type: str = ""
    address: str = ""
    parameters_count: int = 0
    sample_count: int = 0
    method: str = ""
    contact_person: str = ""
    contact_phone: str = ""


class ProtocolTypeIn(BaseModel):
    model_config = {"populate_by_name": True}
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    form_schema_json: str = Field(default="{}", alias="schema_json")
    calculation_schema_json: str = "{}"


class ProtocolTypeOut(ProtocolTypeIn):
    id: str
    version: int
    is_active: bool


class ProtocolIn(BaseModel):
    number: str = Field(min_length=1)
    number_year: int | None = None
    protocol_date: datetime
    protocol_type_id: str
    work_id: str | None = None
    counterparty_id: str
    object_id: str | None = None
    contract_id: str | None = None
    responsible_user_id: str | None = None
    status: str = "draft"


class RowIn(BaseModel):
    section_code: str = "main"
    row_no: int = 1
    values: dict = Field(default_factory=dict)


class ProtocolOut(BaseModel):
    id: str
    number: str
    number_year: int | None
    protocol_date: datetime
    protocol_type_id: str
    work_id: str | None
    counterparty_id: str
    object_id: str | None
    status: str
    form_data: dict
    calculated_data: dict
    rows: list[dict] = []


def _work_out(w: Work) -> WorkOut:
    return WorkOut(
        id=w.id,
        number=w.number,
        number_year=w.number_year,
        work_date=w.work_date,
        counterparty_id=w.counterparty_id,
        object_id=w.object_id,
        contract_id=w.contract_id,
        service_id=w.service_id,
        assignee_user_id=w.assignee_user_id,
        status=w.status,
        notes=w.notes,
        test_type=w.test_type or "",
        address=w.address or "",
        parameters_count=w.parameters_count or 0,
        sample_count=w.sample_count or 0,
        method=w.method or "",
        contact_person=w.contact_person or "",
        contact_phone=w.contact_phone or "",
    )


def _proto_out(p: Protocol, rows: list[ProtocolRow]) -> ProtocolOut:
    return ProtocolOut(
        id=p.id,
        number=p.number,
        number_year=p.number_year,
        protocol_date=p.protocol_date,
        protocol_type_id=p.protocol_type_id,
        work_id=p.work_id,
        counterparty_id=p.counterparty_id,
        object_id=p.object_id,
        status=p.status,
        form_data=json.loads(p.form_data_json or "{}"),
        calculated_data=json.loads(p.calculated_data_json or "{}"),
        rows=[
            {
                "id": r.id,
                "section_code": r.section_code,
                "row_no": r.row_no,
                "values": json.loads(r.values_json or "{}"),
                "calculated": json.loads(r.calculated_json or "{}"),
            }
            for r in sorted(rows, key=lambda x: (x.section_code, x.row_no))
        ],
    )


def _year_of(payload_year: int | None, dt: datetime) -> int:
    return payload_year or dt.year


def _check_unique_number(
    db: Session,
    model: type[Work] | type[Protocol],
    number: str,
    year: int,
    exclude_id: str | None = None,
) -> None:
    stmt = select(model).where(model.number == number, model.number_year == year)
    if exclude_id:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt):
        raise HTTPException(
            status_code=409,
            detail={"code": "NUMBER_CONFLICT", "message": f"Номер {number} в {year} уже занят"},
        )


@router.get("/works", response_model=list[WorkOut])
def list_works(
    q: str = "",
    status: str | None = None,
    test_type: str | None = None,
    counterparty_id: str | None = None,
    assignee_user_id: str | None = None,
    sort: str = "date_desc",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[WorkOut]:
    stmt = select(Work).where(Work.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Work.number.ilike(like)
            | Work.address.ilike(like)
            | Work.test_type.ilike(like)
            | Work.notes.ilike(like)
            | Work.method.ilike(like)
            | Work.contact_person.ilike(like)
            | Work.contact_phone.ilike(like)
        )
    if status:
        stmt = stmt.where(Work.status == status)
    if test_type:
        stmt = stmt.where(Work.test_type == test_type)
    if counterparty_id:
        stmt = stmt.where(Work.counterparty_id == counterparty_id)
    if assignee_user_id:
        stmt = stmt.where(Work.assignee_user_id == assignee_user_id)

    sort_map = {
        "date_desc": Work.work_date.desc(),
        "date_asc": Work.work_date.asc(),
        "number_asc": Work.number.asc(),
        "number_desc": Work.number.desc(),
        "params_desc": Work.parameters_count.desc(),
        "params_asc": Work.parameters_count.asc(),
    }
    order = sort_map.get(sort, Work.work_date.desc())
    rows = db.scalars(stmt.order_by(order).limit(500)).all()
    return [_work_out(w) for w in rows]


@router.post("/works", response_model=WorkOut)
def create_work(
    payload: WorkIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkOut:
    year = _year_of(payload.number_year, payload.work_date)
    _check_unique_number(db, Work, payload.number, year)
    row = Work(**payload.model_dump(exclude={"number_year"}), number_year=year)
    db.add(row)
    write_audit(db, actor_user_id=user.id, action="create", entity_type="work", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _work_out(row)


@router.get("/protocol-types", response_model=list[ProtocolTypeOut])
def list_protocol_types(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProtocolTypeOut]:
    rows = db.scalars(
        select(ProtocolType).where(ProtocolType.is_active.is_(True))
    ).all()
    return [
        ProtocolTypeOut(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            schema_json=r.schema_json,
            calculation_schema_json=r.calculation_schema_json,
            version=r.version,
            is_active=r.is_active,
        )
        for r in rows
    ]


@router.post("/protocol-types", response_model=ProtocolTypeOut)
def create_protocol_type(
    payload: ProtocolTypeIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProtocolTypeOut:
    data = payload.model_dump(by_alias=False)
    row = ProtocolType(
        code=data["code"],
        name=data["name"],
        description=data["description"],
        schema_json=data["form_schema_json"],
        calculation_schema_json=data["calculation_schema_json"],
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="protocol_type",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return ProtocolTypeOut(
        id=row.id,
        code=row.code,
        name=row.name,
        description=row.description,
        schema_json=row.schema_json,
        calculation_schema_json=row.calculation_schema_json,
        version=row.version,
        is_active=row.is_active,
    )


@router.get("/protocols", response_model=list[ProtocolOut])
def list_protocols(
    q: str = "",
    counterparty_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProtocolOut]:
    stmt = select(Protocol).order_by(Protocol.protocol_date.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Protocol.number.ilike(like))
    if counterparty_id:
        stmt = stmt.where(Protocol.counterparty_id == counterparty_id)
    if status:
        stmt = stmt.where(Protocol.status == status)
    rows = db.scalars(stmt.limit(500)).all()
    return [ProtocolOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/protocols", response_model=ProtocolOut)
def create_protocol(
    payload: ProtocolIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProtocolOut:
    year = _year_of(payload.number_year, payload.protocol_date)
    _check_unique_number(db, Protocol, payload.number, year)
    row = Protocol(**payload.model_dump(exclude={"number_year"}), number_year=year)
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="protocol",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _proto_out(row, [])


@router.get("/protocols/{pid}", response_model=ProtocolOut)
def get_protocol(
    pid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProtocolOut:
    row = db.get(Protocol, pid)
    if not row or row.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Протокол не найден"},
        )
    rows = db.scalars(select(ProtocolRow).where(ProtocolRow.protocol_id == pid)).all()
    return _proto_out(row, list(rows))


@router.put("/protocols/{pid}/rows", response_model=ProtocolOut)
def put_rows(
    pid: str,
    payload: list[RowIn],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProtocolOut:
    row = db.get(Protocol, pid)
    if not row or row.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Протокол не найден"},
        )
    existing = db.scalars(select(ProtocolRow).where(ProtocolRow.protocol_id == pid)).all()
    for old in existing:
        db.delete(old)
    db.flush()
    for item in payload:
        db.add(
            ProtocolRow(
                protocol_id=pid,
                section_code=item.section_code,
                row_no=item.row_no,
                values_json=json.dumps(item.values, ensure_ascii=False, default=str),
            )
        )
    db.commit()
    rows = db.scalars(select(ProtocolRow).where(ProtocolRow.protocol_id == pid)).all()
    return _proto_out(row, list(rows))


@router.post("/protocols/{pid}/recalculate", response_model=ProtocolOut)
def recalculate(
    pid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProtocolOut:
    row = db.get(Protocol, pid)
    if not row or row.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Протокол не найден"},
        )

    ptype = db.get(ProtocolType, row.protocol_type_id)
    calc_schema: dict = {}
    if ptype:
        try:
            calc_schema = json.loads(ptype.calculation_schema_json or "{}")
        except json.JSONDecodeError:
            calc_schema = {}

    rows = list(db.scalars(select(ProtocolRow).where(ProtocolRow.protocol_id == pid)).all())
    formulas: dict = calc_schema.get("row_formulas", {})
    summary_formulas: dict = calc_schema.get("summary_formulas", {})

    for r in rows:
        values = json.loads(r.values_json or "{}")
        nums = {
            k: Decimal(str(v))
            for k, v in values.items()
            if isinstance(v, (int, float, str)) and str(v) != ""
        }
        calculated: dict = {}
        for key, expr in formulas.items():
            try:
                calculated[key] = str(eval_formula(expr, nums))
            except FormulaError as exc:
                calculated[key] = f"error: {exc}"
        r.calculated_json = json.dumps(calculated, ensure_ascii=False)

    summary: dict = {}
    all_nums: dict[str, Decimal] = {}
    for r in rows:
        for k, v in json.loads(r.calculated_json or "{}").items():
            try:
                all_nums[f"{r.row_no}_{k}"] = Decimal(str(v))
            except Exception:  # noqa: BLE001
                pass
    for key, expr in summary_formulas.items():
        try:
            summary[key] = str(eval_formula(expr, all_nums))
        except FormulaError as exc:
            summary[key] = f"error: {exc}"

    row.calculated_data_json = json.dumps(summary, ensure_ascii=False)
    row.updated_at = datetime.now(UTC)
    write_audit(
        db,
        actor_user_id=user.id,
        action="recalculate",
        entity_type="protocol",
        entity_id=pid,
    )
    db.commit()
    rows = list(db.scalars(select(ProtocolRow).where(ProtocolRow.protocol_id == pid)).all())
    return _proto_out(row, rows)
