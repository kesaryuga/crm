from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\tasks.py")
t = p.read_text(encoding="utf-8")

if "class TaskPatch" not in t:
    t = t.replace(
        "class CompleteIn(BaseModel):",
        """class TaskPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    task_type: str | None = None
    assignee_user_id: str | None = None
    due_at: datetime | None = None
    priority: str | None = None
    status: str | None = None
    counterparty_id: str | None = None
    object_id: str | None = None
    contract_id: str | None = None
    work_id: str | None = None
    protocol_id: str | None = None


class CompleteIn(BaseModel):""",
        1,
    )

# replace update_task signature to use TaskPatch
t = t.replace(
    """def update_task(
    tid: str,
    payload: TaskIn,""",
    """def update_task(
    tid: str,
    payload: TaskPatch,""",
)

# replace body of update_task model_dump loop
t = t.replace(
    """    prev_assignee = row.assignee_user_id
    for key, val in payload.model_dump().items():
        setattr(row, key, val)""",
    """    prev_assignee = row.assignee_user_id
    for key, val in payload.model_dump(exclude_unset=True).items():
        if val is not None and str(val).strip() == "":
            val = None
        setattr(row, key, val)""",
)

# notification uses payload.title which may be None
t = t.replace(
    'body=payload.title,',
    'body=payload.title or row.title,',
)
t = t.replace(
    'title="Вам назначена задача",\n                body=payload.title,',
    'title="Вам назначена задача",\n                body=payload.title or row.title,',
)

p.write_text(t, encoding="utf-8")
print("task patch ok")
