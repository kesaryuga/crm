from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\tasks.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    '    fk_keys = ("counterparty_id", "object_id", "contract_id", "work_id", "protocol_id", "assignee_user_id")',
    "    fk_keys = (\n"
    '        "counterparty_id",\n'
    '        "object_id",\n'
    '        "contract_id",\n'
    '        "work_id",\n'
    '        "protocol_id",\n'
    '        "assignee_user_id",\n'
    "    )",
)
p.write_text(t, encoding="utf-8")
print("ok")
