from pathlib import Path

for rel, old, new in [
    (
        "backend/app/api/contracts.py",
        '    write_audit(db, actor_user_id=user.id, action="create", entity_type="contract_act", entity_id=act.id)',
        '    write_audit(\n        db, actor_user_id=user.id, action="create", entity_type="contract_act", entity_id=act.id\n    )',
    ),
    (
        "backend/app/main.py",
        '                    "SELECT column_name FROM information_schema.columns WHERE table_name = \'contracts\'"',
        '                    "SELECT column_name FROM information_schema.columns "\n                    "WHERE table_name = \'contracts\'"',
    ),
    (
        "backend/app/models/contract.py",
        '    acts: Mapped[list["ContractAct"]] = relationship(',
        "    acts: Mapped[list[ContractAct]] = relationship(",
    ),
]:
    p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm") / rel
    t = p.read_text(encoding="utf-8")
    if old in t:
        t = t.replace(old, new, 1)
        p.write_text(t, encoding="utf-8")
        print("fixed", rel)
    else:
        print("skip", rel)

# move ContractAct before Contract for type hint without quotes if needed
# actually ContractAct is defined after Contract - need quotes or from __future__
# we already have from __future__ import annotations so unquoted works
print("done")
