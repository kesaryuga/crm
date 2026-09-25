from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\models\protocol.py")
t = p.read_text(encoding="utf-8")
# restore protocol updated_at/deleted_at if missing
if "updated_at: Mapped[datetime | None]" not in t.split("class ProtocolRow")[0]:
    t = t.replace(
        """    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    form_data_json: Mapped[str] = mapped_column(Text, default="{}")
    calculated_data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProtocolRow(Base):""",
        """    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    form_data_json: Mapped[str] = mapped_column(Text, default="{}")
    calculated_data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProtocolRow(Base):""",
    )
p.write_text(t, encoding="utf-8")
print("protocol model restored")
