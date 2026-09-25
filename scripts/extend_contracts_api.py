from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\contracts.py")
t = p.read_text(encoding="utf-8")

# import ContractAct
t = t.replace(
    "from app.models import",
    "from app.models import",
)

# extend ContractIn
t = t.replace(
    """    currency: str = "BYN"
    notes: str = ""
    template_id: str | None = None
""",
    """    currency: str = "BYN"
    notes: str = ""
    execution_days: int = 0
    execution_term: str = ""
    parts_count: int = 1
    template_id: str | None = None
""",
)

# extend ContractOut
t = t.replace(
    """    amount_in_words: str = ""
    items: list[ItemOut] = []
""",
    """    amount_in_words: str = ""
    execution_days: int = 0
    execution_term: str = ""
    parts_count: int = 1
    items: list[ItemOut] = []
    acts: list[dict] = []
""",
)

# _contract_out extras
t = t.replace(
    "        items=[_item_out(i) for i in c.items],",
    "        items=[_item_out(i) for i in c.items],\n        execution_days=c.execution_days or 0,\n        execution_term=c.execution_term or \"\",\n        parts_count=c.parts_count or 1,\n        acts=_acts_out(c),",
)

# add helper and act schemas before _item_out
if "_acts_out" not in t:
    t = t.replace(
        "def _item_out(",
        '''class ActIn(BaseModel):
    title: str = Field(min_length=1)
    act_number: str = ""
    act_date: datetime | None = None
    due_date: datetime | None = None
    amount: Decimal = Decimal("0.00")
    status: str = "planned"
    notes: str = ""


class ActOut(ActIn):
    id: str
    contract_id: str


def _acts_out(c) -> list[dict]:
    acts = getattr(c, "acts", None) or []
    return [
        {
            "id": a.id,
            "contract_id": a.contract_id,
            "title": a.title,
            "act_number": a.act_number or "",
            "act_date": a.act_date.isoformat() if a.act_date else None,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "amount": str(a.amount or 0),
            "status": a.status or "planned",
            "notes": a.notes or "",
        }
        for a in acts
    ]


def _item_out(''',
        1,
    )

# acts endpoints at end of file
if "/contracts/{cid}/acts" not in t:
    t += '''

@router.post("/contracts/{cid}/acts", response_model=ContractOut)
def add_act(
    cid: str,
    payload: ActIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    from app.models import ContractAct

    contract = db.get(Contract, cid)
    if not contract:
        raise _404()
    act = ContractAct(contract_id=cid, **payload.model_dump())
    db.add(act)
    write_audit(db, actor_user_id=user.id, action="create", entity_type="contract_act", entity_id=act.id)
    db.commit()
    db.refresh(contract)
    return _contract_out(contract)


@router.patch("/contracts/{cid}/acts/{aid}", response_model=ContractOut)
def update_act(
    cid: str,
    aid: str,
    payload: ActIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    from app.models import ContractAct

    act = db.get(ContractAct, aid)
    if not act or act.contract_id != cid:
        raise _404("Акт не найден")
    for key, val in payload.model_dump().items():
        setattr(act, key, val)
    db.commit()
    contract = db.get(Contract, cid)
    return _contract_out(contract)


@router.delete("/contracts/{cid}/acts/{aid}", response_model=ContractOut)
def delete_act(
    cid: str,
    aid: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    from app.models import ContractAct

    act = db.get(ContractAct, aid)
    if not act or act.contract_id != cid:
        raise _404("Акт не найден")
    db.delete(act)
    db.commit()
    contract = db.get(Contract, cid)
    return _contract_out(contract)
'''

p.write_text(t, encoding="utf-8")
print("contracts api ok")
