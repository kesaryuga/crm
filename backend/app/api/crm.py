from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import Comment, Contact, Counterparty, SiteObject, User
from app.services import write_audit

router = APIRouter(prefix="/api/v1", tags=["crm"])


class CounterpartyIn(BaseModel):
    full_name: str = Field(min_length=1)
    short_name: str = ""
    unp: str = ""
    legal_address: str = ""
    postal_address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    director_name: str = ""
    director_position: str = ""
    authority_basis: str = ""
    bank_name: str = ""
    bank_bic: str = ""
    bank_account: str = ""
    responsible_user_id: str | None = None
    status: str = "active"
    notes: str = ""


class CounterpartyOut(CounterpartyIn):
    id: str


class ContactIn(BaseModel):
    counterparty_id: str
    full_name: str = Field(min_length=1)
    position: str = ""
    phone: str = ""
    email: str = ""
    is_primary: bool = False
    notes: str = ""


class ContactOut(ContactIn):
    id: str


class ObjectIn(BaseModel):
    counterparty_id: str
    name: str = Field(min_length=1)
    address: str = ""
    contact_id: str | None = None
    phone: str = ""
    description: str = ""
    status: str = "active"


class ObjectOut(ObjectIn):
    id: str


class CommentIn(BaseModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    body: str = Field(min_length=1)
    is_executor_note: bool = False


class CommentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    body: str
    is_executor_note: bool
    author_user_id: str | None
    created_at: datetime | None = None


def _cp_out(row: Counterparty) -> CounterpartyOut:
    return CounterpartyOut(
        id=row.id,
        full_name=row.full_name,
        short_name=row.short_name,
        unp=row.unp,
        legal_address=row.legal_address,
        postal_address=row.postal_address,
        phone=row.phone,
        email=row.email,
        website=row.website,
        director_name=row.director_name,
        director_position=row.director_position,
        authority_basis=row.authority_basis,
        bank_name=row.bank_name,
        bank_bic=row.bank_bic,
        bank_account=row.bank_account,
        responsible_user_id=row.responsible_user_id,
        status=row.status,
        notes=row.notes,
    )


def _cmt_out(c: Comment) -> CommentOut:
    return CommentOut(
        id=c.id,
        created_at=c.created_at,
        entity_type=c.entity_type,
        entity_id=c.entity_id,
        body=c.body,
        is_executor_note=c.is_executor_note,
        author_user_id=c.author_user_id,
    )


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "NOT_FOUND", "message": "Контрагент не найден"},
    )


def _audit(db: Session, user_id: str, action: str, entity_id: str) -> None:
    write_audit(
        db,
        actor_user_id=user_id,
        action=action,
        entity_type="counterparty",
        entity_id=entity_id,
    )


@router.get("/counterparties", response_model=list[CounterpartyOut])
def list_counterparties(
    q: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CounterpartyOut]:
    stmt = select(Counterparty).where(Counterparty.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Counterparty.full_name.ilike(like),
                Counterparty.short_name.ilike(like),
                Counterparty.unp.ilike(like),
                Counterparty.phone.ilike(like),
            )
        )
    rows = db.scalars(stmt.order_by(Counterparty.full_name)).all()
    return [_cp_out(r) for r in rows]


@router.post("/counterparties", response_model=CounterpartyOut)
def create_counterparty(
    payload: CounterpartyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CounterpartyOut:
    row = Counterparty(**payload.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(row)
    _audit(db, user.id, "create", row.id)
    db.commit()
    db.refresh(row)
    return _cp_out(row)


@router.get("/counterparties/{cid}", response_model=CounterpartyOut)
def get_counterparty(
    cid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CounterpartyOut:
    row = db.get(Counterparty, cid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    return _cp_out(row)


@router.patch("/counterparties/{cid}", response_model=CounterpartyOut)
def update_counterparty(
    cid: str,
    payload: CounterpartyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CounterpartyOut:
    row = db.get(Counterparty, cid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    for key, val in payload.model_dump().items():
        setattr(row, key, val)
    row.updated_by = user.id
    _audit(db, user.id, "update", row.id)
    db.commit()
    db.refresh(row)
    return _cp_out(row)


@router.delete("/counterparties/{cid}")
def delete_counterparty(
    cid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    row = db.get(Counterparty, cid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    row.deleted_at = datetime.now(UTC)
    row.deleted_by = user.id
    _audit(db, user.id, "delete", row.id)
    db.commit()
    return {"status": "archived"}


@router.get("/counterparties/{cid}/history")
def counterparty_history(
    cid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CommentOut]:
    rows = db.scalars(
        select(Comment)
        .where(Comment.entity_type == "counterparty", Comment.entity_id == cid)
        .order_by(Comment.created_at)
    ).all()
    return [_cmt_out(c) for c in rows]


@router.post("/contacts", response_model=ContactOut)
def create_contact(
    payload: ContactIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactOut:
    row = Contact(**payload.model_dump())
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="contact",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return ContactOut(id=row.id, **payload.model_dump())


@router.get("/counterparties/{cid}/contacts", response_model=list[ContactOut])
def list_contacts(
    cid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ContactOut]:
    rows = db.scalars(
        select(Contact).where(
            Contact.counterparty_id == cid,
            Contact.deleted_at.is_(None),
        )
    ).all()
    return [
        ContactOut(
            id=r.id,
            counterparty_id=r.counterparty_id,
            full_name=r.full_name,
            position=r.position,
            phone=r.phone,
            email=r.email,
            is_primary=r.is_primary,
            notes=r.notes,
        )
        for r in rows
    ]



@router.patch("/objects/{oid}", response_model=ObjectOut)
def update_object(
    oid: str,
    payload: ObjectIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ObjectOut:
    row = db.get(SiteObject, oid)
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Объект не найден"},
        )
    for key, val in payload.model_dump(exclude={"counterparty_id"}).items():
        setattr(row, key, val)
    write_audit(db, actor_user_id=user.id, action="update", entity_type="object", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return ObjectOut.model_validate(row, from_attributes=True)

@router.post("/objects", response_model=ObjectOut)
def create_object(
    payload: ObjectIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ObjectOut:
    row = SiteObject(**payload.model_dump())
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="object",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return ObjectOut(id=row.id, **payload.model_dump())


@router.get("/counterparties/{cid}/objects", response_model=list[ObjectOut])
def list_objects(
    cid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ObjectOut]:
    rows = db.scalars(
        select(SiteObject).where(
            SiteObject.counterparty_id == cid,
            SiteObject.deleted_at.is_(None),
        )
    ).all()
    return [
        ObjectOut(
            id=r.id,
            counterparty_id=r.counterparty_id,
            name=r.name,
            address=r.address,
            contact_id=r.contact_id,
            phone=r.phone,
            description=r.description,
            status=r.status,
        )
        for r in rows
    ]


@router.post("/comments", response_model=CommentOut)
def create_comment(
    payload: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CommentOut:
    row = Comment(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        body=payload.body,
        is_executor_note=payload.is_executor_note,
        author_user_id=user.id,
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=user.id,
        action="comment",
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
    )
    db.commit()
    db.refresh(row)
    return _cmt_out(row)


@router.get("/comments")
def list_comments(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CommentOut]:
    rows = db.scalars(
        select(Comment)
        .where(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
        .order_by(Comment.created_at)
    ).all()
    return [_cmt_out(c) for c in rows]


@router.get("/search")
def search(
    q: str = Query("", min_length=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, list[dict[str, str]]]:
    if not q:
        return {"counterparties": [], "contacts": [], "objects": []}
    like = f"%{q}%"
    cps = db.scalars(
        select(Counterparty)
        .where(
            Counterparty.deleted_at.is_(None),
            or_(
                Counterparty.full_name.ilike(like),
                Counterparty.short_name.ilike(like),
                Counterparty.unp.ilike(like),
                Counterparty.phone.ilike(like),
                Counterparty.legal_address.ilike(like),
            ),
        )
        .limit(20)
    ).all()
    contacts = db.scalars(
        select(Contact)
        .where(Contact.deleted_at.is_(None), Contact.full_name.ilike(like))
        .limit(20)
    ).all()
    objs = db.scalars(
        select(SiteObject)
        .where(
            SiteObject.deleted_at.is_(None),
            or_(SiteObject.name.ilike(like), SiteObject.address.ilike(like)),
        )
        .limit(20)
    ).all()
    return {
        "counterparties": [
            {"id": c.id, "title": c.full_name, "sub": c.unp} for c in cps
        ],
        "contacts": [
            {"id": c.id, "title": c.full_name, "sub": c.phone} for c in contacts
        ],
        "objects": [
            {"id": o.id, "title": o.name, "sub": o.address} for o in objs
        ],
    }
