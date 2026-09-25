from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\works.py")
t = p.read_text(encoding="utf-8")

t = t.replace(
    '''class WorkIn(BaseModel):
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
''',
    '''class WorkIn(BaseModel):
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
''',
)

t = t.replace(
    '''        assignee_user_id=w.assignee_user_id,
        status=w.status,
        notes=w.notes,
    )''',
    '''        assignee_user_id=w.assignee_user_id,
        status=w.status,
        notes=w.notes,
        test_type=w.test_type or "",
        address=w.address or "",
        parameters_count=w.parameters_count or 0,
        sample_count=w.sample_count or 0,
        method=w.method or "",
        contact_person=w.contact_person or "",
        contact_phone=w.contact_phone or "",
    )''',
)

t = t.replace(
    '''@router.get("/works", response_model=list[WorkOut])
def list_works(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[WorkOut]:
    rows = db.scalars(
        select(Work).where(Work.deleted_at.is_(None)).order_by(Work.work_date.desc())
    ).all()
    return [_work_out(w) for w in rows]''',
    '''@router.get("/works", response_model=list[WorkOut])
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
    return [_work_out(w) for w in rows]''',
)

p.write_text(t, encoding="utf-8")
print("works api ok")
