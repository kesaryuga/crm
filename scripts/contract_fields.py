from pathlib import Path

# 1) Model: execution fields + ContractAct
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\models\contract.py")
t = p.read_text(encoding="utf-8")
if "execution_days" not in t:
    t = t.replace(
        """    notes: Mapped[str] = mapped_column(Text, default="")
    template_id: Mapped[str | None] = mapped_column(String(36), nullable=True)""",
        """    notes: Mapped[str] = mapped_column(Text, default="")
    execution_days: Mapped[int] = mapped_column(Integer, default=0)
    execution_term: Mapped[str] = mapped_column(String(255), default="")
    parts_count: Mapped[int] = mapped_column(Integer, default=1)
    template_id: Mapped[str | None] = mapped_column(String(36), nullable=True)""",
    )
if "from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func" in t:
    t = t.replace(
        "from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func",
        "from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func",
    )
if "class ContractAct" not in t:
    t += '''

class ContractAct(Base):
    """Части / акты по договору."""

    __tablename__ = "contract_acts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    contract_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contracts.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    act_number: Mapped[str] = mapped_column(String(64), default="")
    act_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(32), default="planned")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
'''
p.write_text(t, encoding="utf-8")
print("model ok")

# export ContractAct
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\models\__init__.py")
t = p.read_text(encoding="utf-8")
if "ContractAct" not in t:
    t = t.replace(
        "from app.models.contract import",
        "from app.models.contract import ContractAct,",
    )
    if "ContractAct" not in t:
        t = t.replace(
            "from app.models.contract import Contract, ContractItem, Service",
            "from app.models.contract import Contract, ContractAct, ContractItem, Service",
        )
    t = t.replace('"ContractItem",', '"ContractAct",\n    "ContractItem",')
p.write_text(t, encoding="utf-8")
print("init", "ContractAct" in t)
