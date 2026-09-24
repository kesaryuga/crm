from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import DocumentTemplate, GeneratedDocument, User
from app.services import generate_docx, save_template, write_audit
from app.services.documents import TemplateError

router = APIRouter(prefix="/api/v1", tags=["documents"])


class GenerateIn(BaseModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    context: dict = Field(default_factory=dict)


class TemplateOut(BaseModel):
    id: str
    code: str
    name: str
    document_type: str
    version: int
    is_active: bool
    placeholders: list[str] = []


class GeneratedOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    template_id: str
    template_version: int
    version_no: int
    docx_file_id: str
    hash: str


def _tpl_out(row: DocumentTemplate) -> TemplateOut:
    try:
        meta = json.loads(row.schema_json or "{}")
    except json.JSONDecodeError:
        meta = {}
    return TemplateOut(
        id=row.id,
        code=row.code,
        name=row.name,
        document_type=row.document_type,
        version=row.version,
        is_active=row.is_active,
        placeholders=list(meta.get("placeholders", [])),
    )


def _gen_out(row: GeneratedDocument) -> GeneratedOut:
    return GeneratedOut(
        id=row.id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        template_id=row.template_id,
        template_version=row.template_version,
        version_no=row.version_no,
        docx_file_id=row.docx_file_id,
        hash=row.hash,
    )


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TemplateOut]:
    rows = db.scalars(
        select(DocumentTemplate)
        .where(DocumentTemplate.is_active.is_(True))
        .order_by(DocumentTemplate.code, DocumentTemplate.version.desc())
    ).all()
    return [_tpl_out(r) for r in rows]


@router.post("/templates", response_model=TemplateOut)
async def upload_template(
    code: str = Form(...),
    name: str = Form(...),
    document_type: str = Form("contract"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateOut:
    data = await file.read()
    try:
        row = save_template(
            db,
            code=code,
            name=name,
            document_type=document_type,
            filename=file.filename or "template.docx",
            data=data,
            created_by=user.id,
        )
    except TemplateError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "TEMPLATE_INVALID", "message": str(exc)},
        ) from exc
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="template",
        entity_id=row.id,
    )
    db.commit()
    return _tpl_out(row)


@router.post("/documents/generate", response_model=GeneratedOut)
def generate(
    payload: GenerateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GeneratedOut:
    try:
        row = generate_docx(
            db,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            template_id=payload.template_id,
            context=payload.context,
            generated_by=user.id,
        )
    except TemplateError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "GENERATE_FAILED", "message": str(exc)},
        ) from exc
    write_audit(
        db,
        actor_user_id=user.id,
        action="generate",
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
    )
    db.commit()
    return _gen_out(row)


@router.get("/documents/{entity_type}/{entity_id}", response_model=list[GeneratedOut])
def list_generated(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[GeneratedOut]:
    rows = db.scalars(
        select(GeneratedDocument)
        .where(
            GeneratedDocument.entity_type == entity_type,
            GeneratedDocument.entity_id == entity_id,
        )
        .order_by(GeneratedDocument.version_no.desc())
    ).all()
    return [_gen_out(r) for r in rows]
