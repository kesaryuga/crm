from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\tasks.py")
t = p.read_text(encoding="utf-8")

block = '''

class DelegateIn(BaseModel):
    assignee_user_id: str = Field(min_length=1)
    comment: str = ""


class CalendarItem(BaseModel):
    id: str
    title: str
    due_at: datetime | None
    status: str
    priority: str
    task_type: str
    assignee_user_id: str | None
    is_overdue: bool


@router.post("/tasks/{tid}/delegate", response_model=TaskOut)
def delegate_task(
    tid: str,
    payload: DelegateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = db.get(Task, tid)
    if not row or row.deleted_at is not None:
        raise _not_found()
    if not user.has("tasks.delegate") and not user.has("admin.all") and row.creator_user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Нет права на делегирование"},
        )
    prev = row.assignee_user_id
    row.assignee_user_id = payload.assignee_user_id
    row.status = "in_progress" if row.status == "new" else row.status
    body = payload.comment or "Вам делегирована задача"
    if payload.assignee_user_id != user.id:
        db.add(
            Notification(
                user_id=payload.assignee_user_id,
                type="task_delegated",
                title="Вам делегировали задачу",
                body=f"{row.title}. {body}".strip(),
                entity_type="task",
                entity_id=row.id,
            )
        )
    if prev and prev != user.id and prev != payload.assignee_user_id:
        db.add(
            Notification(
                user_id=prev,
                type="task_reassigned",
                title="Задача передана другому",
                body=row.title,
                entity_type="task",
                entity_id=row.id,
            )
        )
    write_audit(db, actor_user_id=user.id, action="delegate", entity_type="task", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _task_out(row)


@router.get("/tasks/calendar", response_model=list[CalendarItem])
def tasks_calendar(
    date_from: str | None = None,
    date_to: str | None = None,
    assignee_user_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CalendarItem]:
    from datetime import datetime as dt

    def parse(v: str | None) -> dt | None:
        if not v:
            return None
        try:
            return dt.fromisoformat(v)
        except ValueError:
            return None

    start = parse(date_from) or datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    end = parse(date_to)
    stmt = select(Task).where(Task.deleted_at.is_(None), Task.due_at.is_not(None))
    stmt = stmt.where(Task.due_at >= start)
    if end:
        stmt = stmt.where(Task.due_at <= end)
    if assignee_user_id:
        stmt = stmt.where(Task.assignee_user_id == assignee_user_id)
    rows = db.scalars(stmt.order_by(Task.due_at.asc()).limit(500)).all()
    return [
        CalendarItem(
            id=t.id,
            title=t.title,
            due_at=t.due_at,
            status=t.status,
            priority=t.priority,
            task_type=t.task_type,
            assignee_user_id=t.assignee_user_id,
            is_overdue=t.is_overdue,
        )
        for t in rows
    ]


@router.get("/tasks/upcoming", response_model=list[TaskOut])
def tasks_upcoming(
    hours: int = 48,
    assignee_user_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskOut]:
    now = datetime.now(UTC)
    until = now + timedelta(hours=max(1, min(hours, 24 * 14)))
    stmt = select(Task).where(
        Task.deleted_at.is_(None),
        Task.due_at.is_not(None),
        Task.status.notin_(("done", "cancelled")),
        Task.due_at >= now,
        Task.due_at <= until,
    )
    target = assignee_user_id or user.id
    stmt = stmt.where(or_(Task.assignee_user_id == target, Task.creator_user_id == user.id))
    rows = list(db.scalars(stmt.order_by(Task.due_at.asc()).limit(200)).all())

    # reminders: notify once per task/day window
    for t in rows:
        if t.assignee_user_id and t.due_at is not None:
            existing = db.scalar(
                select(Notification).where(
                    Notification.user_id == t.assignee_user_id,
                    Notification.type == "task_reminder",
                    Notification.entity_id == t.id,
                )
            )
            if not existing and t.due_at - now <= timedelta(hours=24):
                db.add(
                    Notification(
                        user_id=t.assignee_user_id,
                        type="task_reminder",
                        title="Напоминание о сроке",
                        body=t.title,
                        entity_type="task",
                        entity_id=t.id,
                    )
                )
    db.commit()
    return [_task_out(t) for t in rows]

'''

if "/tasks/calendar" in t:
    print("already")
else:
    # insert before notifications if present, else append
    marker = '@router.get("/notifications")'
    if marker in t:
        t = t.replace(marker, block + "\n" + marker, 1)
    else:
        t = t + block
    # ensure timedelta import
    if "timedelta" not in t.split("\n")[0:15].__str__():
        t = t.replace(
            "from datetime import datetime, timezone",
            "from datetime import datetime, timedelta, timezone",
        )
    # common import styles
    if "from datetime import UTC, datetime" in t and "timedelta" not in t.split("from datetime")[1].split("\n")[0]:
        t = t.replace("from datetime import UTC, datetime", "from datetime import UTC, datetime, timedelta")
    p.write_text(t, encoding="utf-8")
    print("inserted")
print("imports check:", [ln for ln in t.splitlines() if "datetime" in ln][:5])
