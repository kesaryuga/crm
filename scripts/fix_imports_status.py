from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\tasks.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    '    for key in ("counterparty_id", "object_id", "contract_id", "work_id", "protocol_id", "assignee_user_id"):',
    '    fk_keys = ("counterparty_id", "object_id", "contract_id", "work_id", "protocol_id", "assignee_user_id")\n'
    "    for key in fk_keys:",
)
p.write_text(t, encoding="utf-8")
print("tasks line ok")

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\app\(app)\counterparties\[id]\page.tsx")
t = p.read_text(encoding="utf-8")
if "Select," not in t.split("} from \"@/components/ui\";")[0]:
    t = t.replace(
        "  Spinner,\n  Table,\n  Textarea,\n} from \"@/components/ui\";",
        "  Select,\n  Spinner,\n  Table,\n  Textarea,\n} from \"@/components/ui\";",
    )
print("select import", "Select," in t)
# status select check
print("status select", "CP_STATUSES" in t and "form.status || \"active\"" in t)
p.write_text(t, encoding="utf-8")
