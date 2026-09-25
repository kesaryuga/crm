from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\works.py")
text = p.read_text(encoding="utf-8")
needle = '@router.post("/protocols", response_model=ProtocolOut)'
insert = """@router.get("/protocols", response_model=list[ProtocolOut])
def list_protocols(
    q: str = "",
    counterparty_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProtocolOut]:
    stmt = select(Protocol).order_by(Protocol.protocol_date.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Protocol.number.ilike(like))
    if counterparty_id:
        stmt = stmt.where(Protocol.counterparty_id == counterparty_id)
    if status:
        stmt = stmt.where(Protocol.status == status)
    rows = db.scalars(stmt.limit(500)).all()
    return [ProtocolOut.model_validate(r, from_attributes=True) for r in rows]


"""
if '@router.get("/protocols"' in text:
    print("already present")
else:
    if needle not in text:
        raise SystemExit("needle missing")
    text = text.replace(needle, insert + needle, 1)
    p.write_text(text, encoding="utf-8")
    print("inserted")
