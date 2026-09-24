from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import Comment, Counterparty, Notification, SiteObject, Task, User
from app.services import write_audit

router = APIRouter(prefix="/api/v1", tags=["tasks"])

DONE = ("completed", "cancelled")


class TaskIn(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    task_type: str = "other"
    assignee_user_id: str | None = None
    due_at: datetime | None = None
    priority: str = "medium"
    status: str = "new"
    counterparty_id: str | None = None
    object_id: str | None = None
    contract_id: str | None = None
    work_id: str | None = None
    protocol_id: str | None = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    task_type: str
    creator_user_id: str | None
    assignee_user_id: str | None
    due_at: datetime | None
    priority: str
    status: str
    completed_at: datetime | None
    is_overdue: bool
    counterparty_id: str | None = None
    object_id: str | None = None


class CompleteIn(BaseModel):
    comment: str = ""


def _task_out(t: Task) -> TaskOut:
    return TaskOut(
        id=t.id,
        title=t.title,
        description=t.description,
        task_type=t.task_type,
        creator_user_id=t.creator_user_id,
        assignee_user_id=t.assignee_user_id,
        due_at=t.due_at,
        priority=t.priority,
        status=t.status,
        completed_at=t.completed_at,
        is_overdue=t.is_overdue,
        counterparty_id=t.counterparty_id,
        object_id=t.object_id,
    )


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "NOT_FOUND", "message": "Задача не найдена"},
    )


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    assignee_user_id: str | None = None,
    overdue: bool = False,
    q: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskOut]:
    stmt = select(Task).where(Task.deleted_at.is_(None))
    if status:
        stmt = stmt.where(Task.status == status)
    if assignee_user_id:
        stmt = stmt.where(Task.assignee_user_id == assignee_user_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
    rows = list(db.scalars(stmt.order_by(Task.created_at.desc())).all())
    if overdue:
        rows = [t for t in rows if t.is_overdue]
    return [_task_out(t) for t in rows]


@router.post("/tasks", response_model=TaskOut)
def create_task(
    payload: TaskIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = Task(**payload.model_dump(), creator_user_id=user.id)
    db.add(row)
    if payload.assignee_user_id and payload.assignee_user_id != user.id:
        db.add(
            Notification(
                user_id=payload.assignee_user_id,
                type="task_assigned",
                title="Новая задача",
                body=payload.title,
                entity_type="task",
                entity_id=row.id,
            )
        )
    write_audit(
        db,
        actor_user_id=user.id,
        action="create",
        entity_type="task",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _task_out(row)


@router.get("/tasks/{tid}", response_model=TaskOut)
def get_task(
    tid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = db.get(Task, tid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    return _task_out(row)


@router.patch("/tasks/{tid}", response_model=TaskOut)
def update_task(
    tid: str,
    payload: TaskIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = db.get(Task, tid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    prev_assignee = row.assignee_user_id
    for key, val in payload.model_dump().items():
        setattr(row, key, val)
    if (
        payload.assignee_user_id
        and payload.assignee_user_id != prev_assignee
        and payload.assignee_user_id != user.id
    ):
        db.add(
            Notification(
                user_id=payload.assignee_user_id,
                type="task_assigned",
                title="Вам назначена задача",
                body=payload.title,
                entity_type="task",
                entity_id=row.id,
            )
        )
    write_audit(
        db,
        actor_user_id=user.id,
        action="update",
        entity_type="task",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _task_out(row)


@router.post("/tasks/{tid}/complete", response_model=TaskOut)
def complete_task(
    tid: str,
    payload: CompleteIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = db.get(Task, tid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    row.status = "completed"
    row.completed_at = datetime.now(UTC)
    body = payload.comment if payload else ""
    if body:
        db.add(
            Comment(
                entity_type="task",
                entity_id=row.id,
                body=body,
                author_user_id=user.id,
            )
        )
    write_audit(
        db,
        actor_user_id=user.id,
        action="complete",
        entity_type="task",
        entity_id=row.id,
    )
    db.commit()
    db.refresh(row)
    return _task_out(row)


@router.post("/tasks/{tid}/comments")
def comment_task(
    tid: str,
    body: str = Query(..., min_length=1),
    is_executor_note: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    row = db.get(Task, tid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    db.add(
        Comment(
            entity_type="task",
            entity_id=row.id,
            body=body,
            is_executor_note=is_executor_note,
            author_user_id=user.id,
        )
    )
    db.commit()
    return {"status": "ok"}


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    open_statuses = ("new", "in_progress")

    tasks = list(db.scalars(select(Task).where(Task.deleted_at.is_(None))).all())
    overdue = [t for t in tasks if t.is_overdue]
    due_today = [
        t
        for t in tasks
        if t.due_at is not None
        and t.status not in DONE
        and t.due_at >= today_start
        and t.due_at < today_start.replace(hour=23, minute=59, second=59)
    ]
    mine = [t for t in tasks if t.assignee_user_id == user.id and t.status in open_statuses]

    cps = db.scalar(
        select(func.count()).select_from(Counterparty).where(Counterparty.deleted_at.is_(None))
    )
    objs = db.scalar(
        select(func.count()).select_from(SiteObject).where(SiteObject.deleted_at.is_(None))
    )

    return {
        "tasks_today": len(due_today),
        "overdue": len(overdue),
        "my_open_tasks": len(mine),
        "counterparties": cps or 0,
        "objects": objs or 0,
        "overdue_tasks": [
            {"id": t.id, "title": t.title, "due_at": t.due_at, "priority": t.priority}
            for t in overdue[:10]
        ],
        "my_tasks": [
            {"id": t.id, "title": t.title, "due_at": t.due_at, "status": t.status}
            for t in sorted(mine, key=lambda x: x.due_at or now)[:10]
        ],
    }


@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, object]]:
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "read_at": n.read_at,
            "created_at": n.created_at,
        }
        for n in rows
    ]
