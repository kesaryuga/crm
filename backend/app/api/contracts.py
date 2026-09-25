from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import Contract, ContractItem, Service, User
from app.services import amount_in_words, line_totals, recalculate_contract, write_audit

router = APIRouter(prefix="/api/v1", tags=["contracts"])


class ServiceIn(BaseModel):
    code: str = ""
    category: str = ""
    name: str = Field(min_length=1)
    description: str = ""
    unit: str = "шт"
    base_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = "BYN"
    vat_rate: Decimal | None = None
    is_active: bool = True


class ServiceOut(ServiceIn):
    id: str


class ItemIn(BaseModel):
    service_id: str | None = None
    name_snapshot: str = Field(min_length=1)
    unit_snapshot: str = "шт"
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_type: str | None = None
    discount_value: Decimal | None = None
    vat_rate: Decimal | None = None
    sort_order: int = 0


class ItemOut(ItemIn):
    id: str
    subtotal: Decimal
    vat_amount: Decimal
    total: Decimal


class ContractIn(BaseModel):
    number: str = Field(min_length=1)
    series: str = ""
    number_year: int | None = None
    contract_date: datetime
    counterparty_id: str
    object_id: str | None = None
    responsible_user_id: str | None = None
    status: str = "draft"
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    currency: str = "BYN"
    notes: str = ""
    execution_days: int = 0
    execution_term: str = ""
    parts_count: int = 1
    template_id: str | None = None


class ContractOut(BaseModel):
    id: str
    number: str
    series: str
    number_year: int | None
    contract_date: datetime
    counterparty_id: str
    object_id: str | None
    responsible_user_id: str | None
    status: str
    valid_from: datetime | None
    valid_to: datetime | None
    currency: str
    subtotal: Decimal
    vat_amount: Decimal
    total_amount: Decimal
    notes: str
    amount_in_words: str = ""
    execution_days: int = 0
    execution_term: str = ""
    parts_count: int = 1
    items: list[ItemOut] = []
    acts: list[dict] = []


class ActIn(BaseModel):
    title: str = Field(min_length=1)
    act_number: str = ""
    act_date: datetime | None = None
    due_date: datetime | None = None
    amount: Decimal = Decimal("0.00")
    status: str = "planned"
    notes: str = ""


class ActOut(ActIn):
    id: str
    contract_id: str


def _acts_out(c) -> list[dict]:
    acts = getattr(c, "acts", None) or []
    return [
        {
            "id": a.id,
            "contract_id": a.contract_id,
            "title": a.title,
            "act_number": a.act_number or "",
            "act_date": a.act_date.isoformat() if a.act_date else None,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "amount": str(a.amount or 0),
            "status": a.status or "planned",
            "notes": a.notes or "",
        }
        for a in acts
    ]


def _item_out(i: ContractItem) -> ItemOut:
    return ItemOut(
        id=i.id,
        service_id=i.service_id,
        name_snapshot=i.name_snapshot,
        unit_snapshot=i.unit_snapshot,
        quantity=i.quantity,
        unit_price=i.unit_price,
        discount_type=i.discount_type,
        discount_value=i.discount_value,
        vat_rate=i.vat_rate,
        subtotal=i.subtotal,
        vat_amount=i.vat_amount,
        total=i.total,
        sort_order=i.sort_order,
    )


def _contract_out(c: Contract) -> ContractOut:
    return ContractOut(
        id=c.id,
        number=c.number,
        series=c.series,
        number_year=c.number_year,
        contract_date=c.contract_date,
        counterparty_id=c.counterparty_id,
        object_id=c.object_id,
        responsible_user_id=c.responsible_user_id,
        status=c.status,
        valid_from=c.valid_from,
        valid_to=c.valid_to,
        currency=c.currency,
        subtotal=c.subtotal,
        vat_amount=c.vat_amount,
        total_amount=c.total_amount,
        notes=c.notes,
        amount_in_words=amount_in_words(c.total_amount, c.currency),
        items=[_item_out(i) for i in sorted(c.items, key=lambda x: x.sort_order)],
    )


def _recalc(db: Session, contract: Contract) -> None:
    totals = [
        line_totals(i.quantity, i.unit_price, i.discount_type, i.discount_value, i.vat_rate)
        for i in contract.items
    ]
    for item, (sub, vat, tot) in zip(contract.items, totals, strict=False):
        item.subtotal, item.vat_amount, item.total = sub, vat, tot
    contract.subtotal, contract.vat_amount, contract.total_amount = recalculate_contract(totals)


def _404(msg: str = "Договор не найден") -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": msg})


@router.get("/services", response_model=list[ServiceOut])
def list_services(
    q: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ServiceOut]:
    stmt = select(Service).where(Service.deleted_at.is_(None), Service.is_active.is_(True))
    if q:
        stmt = stmt.where(Service.name.ilike(f"%{q}%"))
    rows = db.scalars(stmt.order_by(Service.name)).all()
    return [
        ServiceOut(
            id=s.id,
            code=s.code,
            category=s.category,
            name=s.name,
            description=s.description,
            unit=s.unit,
            base_price=s.base_price,
            currency=s.currency,
            vat_rate=s.vat_rate,
            is_active=s.is_active,
        )
        for s in rows
    ]


@router.post("/services", response_model=ServiceOut)
def create_service(
    payload: ServiceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ServiceOut:
    row = Service(**payload.model_dump())
    db.add(row)
    write_audit(db, actor_user_id=user.id, action="create", entity_type="service", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return ServiceOut(id=row.id, **payload.model_dump())


@router.get("/contracts", response_model=list[ContractOut])
def list_contracts(
    status: str | None = None,
    counterparty_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ContractOut]:
    stmt = select(Contract).where(Contract.deleted_at.is_(None))
    if status:
        stmt = stmt.where(Contract.status == status)
    if counterparty_id:
        stmt = stmt.where(Contract.counterparty_id == counterparty_id)
    rows = db.scalars(stmt.order_by(Contract.contract_date.desc())).all()
    return [_contract_out(c) for c in rows]


@router.post("/contracts", response_model=ContractOut)
def create_contract(
    payload: ContractIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    year = payload.number_year or payload.contract_date.year
    exists = db.scalar(
        select(Contract).where(
            Contract.number == payload.number,
            Contract.number_year == year,
            Contract.deleted_at.is_(None),
        )
    )
    if exists:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTRACT_NUMBER_CONFLICT",
                "message": f"Номер {payload.number} в {year} уже занят",
            },
        )
    data = payload.model_dump(exclude={"number_year"})
    row = Contract(**data, number_year=year, created_by=user.id)
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="contract",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _contract_out(row)


@router.get("/contracts/{cid}", response_model=ContractOut)
def get_contract(
    cid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    row = db.get(Contract, cid)
    if not row or row.deleted_at is not None:
        raise _404()
    return _contract_out(row)


@router.patch("/contracts/{cid}", response_model=ContractOut)
def update_contract(
    cid: str,
    payload: ContractIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    row = db.get(Contract, cid)
    if not row or row.deleted_at is not None:
        raise _404()
    data = payload.model_dump(exclude={"number_year"})
    year = payload.number_year or payload.contract_date.year
    if data["number"] != row.number or year != row.number_year:
        exists = db.scalar(
            select(Contract).where(
                Contract.number == data["number"],
                Contract.number_year == year,
                Contract.id != cid,
                Contract.deleted_at.is_(None),
            )
        )
        if exists:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "CONTRACT_NUMBER_CONFLICT",
                    "message": f"Номер {data['number']} в {year} уже занят",
                },
            )
    for key, val in data.items():
        setattr(row, key, val)
    row.number_year = year
    write_audit(
        db,
        actor_user_id=user.id,
        action="update",
        entity_type="contract",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _contract_out(row)


@router.post("/contracts/{cid}/items", response_model=ContractOut)
def add_item(
    cid: str,
    payload: ItemIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    row = db.get(Contract, cid)
    if not row or row.deleted_at is not None:
        raise _404()
    data = payload.model_dump()
    if data.get("service_id") and not data.get("name_snapshot"):
        svc = db.get(Service, data["service_id"])
        if svc:
            data["name_snapshot"] = svc.name
            data["unit_snapshot"] = svc.unit
            data["unit_price"] = svc.base_price
    item = ContractItem(contract_id=cid, **data)
    row.items.append(item)
    db.flush()
    _recalc(db, row)
    write_audit(db, actor_user_id=user.id, action="add_item", entity_type="contract", entity_id=cid)
    db.commit()
    db.refresh(row)
    return _contract_out(row)


@router.post("/contracts/{cid}/acts", response_model=ContractOut)
def add_act(
    cid: str,
    payload: ActIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    from app.models import ContractAct

    contract = db.get(Contract, cid)
    if not contract:
        raise _404()
    act = ContractAct(contract_id=cid, **payload.model_dump())
    db.add(act)
    write_audit(
        db, actor_user_id=user.id, action="create", entity_type="contract_act", entity_id=act.id
    )
    db.commit()
    db.refresh(contract)
    return _contract_out(contract)


@router.patch("/contracts/{cid}/acts/{aid}", response_model=ContractOut)
def update_act(
    cid: str,
    aid: str,
    payload: ActIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    from app.models import ContractAct

    act = db.get(ContractAct, aid)
    if not act or act.contract_id != cid:
        raise _404("Акт не найден")
    for key, val in payload.model_dump().items():
        setattr(act, key, val)
    db.commit()
    contract = db.get(Contract, cid)
    return _contract_out(contract)


@router.delete("/contracts/{cid}/acts/{aid}", response_model=ContractOut)
def delete_act(
    cid: str,
    aid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    from app.models import ContractAct

    act = db.get(ContractAct, aid)
    if not act or act.contract_id != cid:
        raise _404("Акт не найден")
    db.delete(act)
    db.commit()
    contract = db.get(Contract, cid)
    return _contract_out(contract)
