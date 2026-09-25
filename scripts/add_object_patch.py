from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\crm.py")
t = p.read_text(encoding="utf-8")

if 'router.patch("/objects/' not in t:
    # add after list_objects or at end before search
    block = '''
@router.patch("/objects/{oid}", response_model=ObjectOut)
def update_object(
    oid: str,
    payload: ObjectIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ObjectOut:
    row = db.get(SiteObject, oid)
    if not row:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Объект не найден"})
    for key, val in payload.model_dump(exclude={"counterparty_id"}).items():
        setattr(row, key, val)
    write_audit(db, actor_user_id=user.id, action="update", entity_type="object", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return ObjectOut.model_validate(row, from_attributes=True)

'''
    t = t.replace('@router.post("/objects"', block + '@router.post("/objects"', 1)

# CommentOut created_at
if "created_at" not in t.split("class CommentOut")[1][:200]:
    t = t.replace(
        """class CommentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    body: str
    is_executor_note: bool
    author_user_id: str | None
""",
        """class CommentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    body: str
    is_executor_note: bool
    author_user_id: str | None
    created_at: datetime | None = None
""",
    )

# _cmt_out include created_at
t = t.replace(
    """    return CommentOut(
        id=c.id,""",
    """    return CommentOut(
        id=c.id,
        created_at=c.created_at,""",
)

p.write_text(t, encoding="utf-8")
print("crm api ok")
