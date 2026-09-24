from __future__ import annotations

import json
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import DocumentTemplate, File, GeneratedDocument
from app.storage import LocalStorage, sha256_hex

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")

ALLOWED_EXT = {".docx", ".doc"}


class TemplateError(ValueError):
    pass


def extract_placeholders(text: str) -> list[str]:
    return sorted(set(PLACEHOLDER_RE.findall(text)))


def find_placeholders_in_docx(data: bytes) -> list[str]:
    """Найти {{ var }} в тексте DOCX (через python-docx / zip xml)."""
    import io
    import zipfile

    names: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml = zf.read(name).decode("utf-8", errors="ignore")
                names.update(extract_placeholders(xml))
    return sorted(names)


def get_storage() -> LocalStorage:
    from app.core.config import get_settings

    return LocalStorage(get_settings().storage_local_path)


def save_template(
    db: Session,
    *,
    code: str,
    name: str,
    document_type: str,
    filename: str,
    data: bytes,
    created_by: str | None,
    schema: dict | None = None,
) -> DocumentTemplate:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise TemplateError("Допускаются только Word-файлы .docx/.doc")

    storage = get_storage()
    key = storage.put(data, filename)
    file_row = File(
        original_name=filename,
        storage_key=key,
        storage_backend=storage.backend,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=len(data),
        sha256=sha256_hex(data),
        uploaded_by=created_by,
    )
    db.add(file_row)
    db.flush()

    placeholders = find_placeholders_in_docx(data)
    known = set((schema or {}).get("fields", {}))
    unknown = [p for p in placeholders if p not in known] if known else []

    last = db.query(DocumentTemplate).filter(DocumentTemplate.code == code).count()
    row = DocumentTemplate(
        code=code,
        name=name,
        document_type=document_type,
        version=last + 1,
        file_id=file_row.id,
        schema_json=json.dumps(
            {
                "placeholders": placeholders,
                "unknown": unknown,
                "fields": (schema or {}).get("fields", {}),
            },
            ensure_ascii=False,
        ),
        created_by=created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def generate_docx(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    template_id: str,
    context: dict,
    generated_by: str | None,
) -> GeneratedDocument:
    template = db.get(DocumentTemplate, template_id)
    if not template or not template.is_active:
        raise TemplateError("Шаблон не найден или неактивен")

    tpl_file = db.get(File, template.file_id)
    if not tpl_file or tpl_file.is_deleted:
        raise TemplateError("Файл шаблона недоступен")

    storage = get_storage()
    raw = storage.get(tpl_file.storage_key)

    try:
        import io

        from docxtpl import DocxTemplate

        doc = DocxTemplate(io.BytesIO(raw))
        doc.render(context)
        buf = io.BytesIO()
        doc.save(buf)
        out_bytes = buf.getvalue()
    except ImportError:
        out_bytes = raw
    except Exception as exc:  # noqa: BLE001
        raise TemplateError(f"Ошибка генерации: {exc}") from exc

    out_name = f"{entity_type}_{entity_id}_v{template.version}.docx"
    key = storage.put(out_bytes, out_name)
    file_row = File(
        original_name=out_name,
        storage_key=key,
        storage_backend=storage.backend,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=len(out_bytes),
        sha256=sha256_hex(out_bytes),
        uploaded_by=generated_by,
    )
    db.add(file_row)
    db.flush()

    prev = (
        db.query(GeneratedDocument)
        .filter(
            GeneratedDocument.entity_type == entity_type,
            GeneratedDocument.entity_id == entity_id,
            GeneratedDocument.template_id == template_id,
        )
        .count()
    )
    row = GeneratedDocument(
        entity_type=entity_type,
        entity_id=entity_id,
        template_id=template_id,
        template_version=template.version,
        version_no=prev + 1,
        docx_file_id=file_row.id,
        data_snapshot_json=json.dumps(context, ensure_ascii=False, default=str),
        generated_by=generated_by,
        hash=sha256_hex(out_bytes),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
