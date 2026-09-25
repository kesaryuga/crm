from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\models\contract.py")
t = p.read_text(encoding="utf-8")
if "acts: Mapped[list[ContractAct]]" not in t:
    t = t.replace(
        """    items: Mapped[list[ContractItem]] = relationship(
        back_populates="contract", lazy="selectin", cascade="all, delete-orphan"
    )""",
        """    items: Mapped[list[ContractItem]] = relationship(
        back_populates="contract", lazy="selectin", cascade="all, delete-orphan"
    )
    acts: Mapped[list["ContractAct"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", order_by="ContractAct.due_date"
    )""",
    )
p.write_text(t, encoding="utf-8")
print("relation ok")

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\main.py")
t = p.read_text(encoding="utf-8")
if "_ensure_contract_columns" not in t:
    t = t.replace(
        "def _ensure_work_columns()",
        '''def _ensure_contract_columns() -> None:
    engine = get_engine()
    cols = {
        "execution_days": "INTEGER DEFAULT 0",
        "execution_term": "VARCHAR(255) DEFAULT ''",
        "parts_count": "INTEGER DEFAULT 1",
    }
    try:
        with engine.begin() as conn:
            existing = {
                row[0]
                for row in conn.exec_driver_sql(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'contracts'"
                )
            }
            for name, ddl in cols.items():
                if name not in existing:
                    conn.exec_driver_sql(
                        f"ALTER TABLE contracts ADD COLUMN IF NOT EXISTS {name} {ddl}"
                    )
    except Exception:
        pass


def _ensure_work_columns()''',
        1,
    )
    t = t.replace(
        "    _ensure_work_columns()",
        "    _ensure_work_columns()\n    _ensure_contract_columns()",
    )
p.write_text(t, encoding="utf-8")
print("migration ok")
