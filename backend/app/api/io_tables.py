from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import Contract, Counterparty, Task, User
from app.services import write_audit
from app.services.io_tables import (
    CP_COLUMNS,
    contracts_to_csv,
    counterparties_to_csv,
    counterparties_to_xlsx,
    parse_counterparties_csv,
    tasks_to_csv,
)

router = APIRouter(prefix="/api/v1", tags=["io"])


@router.post("/import/counterparties/preview")
async def import_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = await file.read()
    try:
        rows = parse_counterparties_csv(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail={"code": "PARSE_ERROR", "message": f"Не удалось прочитать файл: {exc}"},
        ) from exc
    return {
        "columns": [{"key": k, "label": v} for k, v in CP_COLUMNS.items()],
        "rows": rows[:50],
        "total": len(rows),
        "required": ["full_name"],
    }


@router.post("/import/counterparties")
async def import_commit(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = await file.read()
    rows = parse_counterparties_csv(data)
    created = 0
    skipped = 0
    for row in rows:
        if not row.get("full_name"):
            skipped += 1
            continue
        exists = db.scalar(
            select(Counterparty).where(
                Counterparty.full_name == row["full_name"],
                Counterparty.unp == row.get("unp", ""),
                Counterparty.deleted_at.is_(None),
            )
        )
        if exists:
            skipped += 1
            continue
        db.add(
            Counterparty(
                full_name=row["full_name"],
                short_name=row.get("short_name", ""),
                unp=row.get("unp", ""),
                phone=row.get("phone", ""),
                email=row.get("email", ""),
                legal_address=row.get("legal_address", ""),
                notes=row.get("notes", ""),
                created_by=user.id,
                updated_by=user.id,
            )
        )
        created += 1
    write_audit(
        db,
        actor_user_id=user.id,
        action="import",
        entity_type="counterparty",
        entity_id=None,
        details={"created": created, "skipped": skipped},
    )
    db.commit()
    return {"created": created, "skipped": skipped}


@router.get("/export/counterparties.csv")
def export_counterparties_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    rows = db.scalars(
        select(Counterparty).where(Counterparty.deleted_at.is_(None))
    ).all()
    text = counterparties_to_csv(rows)
    return Response(
        content=text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=counterparties.csv"},
    )


@router.get("/export/counterparties.xlsx")
def export_counterparties_xlsx(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    rows = db.scalars(
        select(Counterparty).where(Counterparty.deleted_at.is_(None))
    ).all()
    try:
        payload = counterparties_to_xlsx(rows)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=501,
            detail={"code": "XLSX_UNAVAILABLE", "message": str(exc)},
        ) from exc
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=counterparties.xlsx"},
    )


@router.get("/export/tasks.csv")
def export_tasks_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    rows = db.scalars(select(Task).where(Task.deleted_at.is_(None))).all()
    return Response(
        content=tasks_to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"},
    )


@router.get("/export/contracts.csv")
def export_contracts_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    rows = db.scalars(select(Contract).where(Contract.deleted_at.is_(None))).all()
    return Response(
        content=contracts_to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=contracts.csv"},
    )
