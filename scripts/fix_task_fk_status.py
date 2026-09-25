from pathlib import Path

# 1) Backend: normalize optional FKs and validate counterparty
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\tasks.py")
t = p.read_text(encoding="utf-8")
old = '''    row = Task(**payload.model_dump(), creator_user_id=user.id)
    db.add(row)'''
new = '''    data = payload.model_dump()
    for key in ("counterparty_id", "object_id", "contract_id", "work_id", "protocol_id", "assignee_user_id"):
        val = data.get(key)
        if val is not None and str(val).strip() == "":
            data[key] = None
        elif val is not None:
            data[key] = str(val).strip()
    if data.get("counterparty_id"):
        from app.models import Counterparty

        exists = db.get(Counterparty, data["counterparty_id"])
        if not exists:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "BAD_COUNTERPARTY",
                    "message": "Контрагент не найден — выберите из списка",
                },
            )
    row = Task(**data, creator_user_id=user.id)
    db.add(row)'''
if old not in t:
    raise SystemExit("create_task pattern missing")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("tasks.py ok")

# 2) Frontend tasks: counterparty Select
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\app\(app)\tasks\page.tsx")
t = p.read_text(encoding="utf-8")
t = t.replace(
    '''          <Field label="ID контрагента (необязательно)">
            <Input
              value={form.counterparty_id}
              onChange={(e) => setForm({ ...form, counterparty_id: e.target.value })}
              placeholder="можно оставить пустым"
            />
          </Field>''',
    '''          <Field label="Контрагент (необязательно)">
            <Select
              value={form.counterparty_id}
              onChange={(e) => setForm({ ...form, counterparty_id: e.target.value })}
            >
              <option value="">— без контрагента —</option>
              {counterparties.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </Select>
          </Field>''',
)
if "const [counterparties" not in t:
    t = t.replace(
        "  const [users, setUsers] = useState<User[]>([]);",
        "  const [users, setUsers] = useState<User[]>([]);\n  const [counterparties, setCounterparties] = useState<{ id: string; full_name: string }[]>([]);",
    )
    t = t.replace(
        "      const [list, u] = await Promise.all([\n        apiGet<Task[]>(`/tasks${params.toString() ? `?${params}` : \"\"}`),\n        apiGet<User[]>(`/users`).catch(() => []),\n      ]);",
        "      const [list, u, cps] = await Promise.all([\n        apiGet<Task[]>(`/tasks${params.toString() ? `?${params}` : \"\"}`),\n        apiGet<User[]>(`/users`).catch(() => []),\n        apiGet<{ id: string; full_name: string }[]>(`/counterparties`).catch(() => []),\n      ]);",
    )
    t = t.replace(
        "      setUsers(u);",
        "      setUsers(u);\n      setCounterparties(cps);",
    )
p.write_text(t, encoding="utf-8")
print("tasks page ok")

# 3) Counterparty edit status Select
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\app\(app)\counterparties\[id]\page.tsx")
t = p.read_text(encoding="utf-8")
t = t.replace(
    '''          <Field label="Статус">
            <Input value={form.status || ""} onChange={(e) => setForm({ ...form, status: e.target.value })} />
          </Field>''',
    '''          <Field label="Статус">
            <Select
              value={form.status || "active"}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              {Object.entries(CP_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>''',
)
if "import {" in t and "Select" not in t.split("from \"@/components/ui\"")[0].split("import {")[-1]:
    t = t.replace(
        "  Spinner,\n  Table,\n  Textarea,\n} from \"@/components/ui\";",
        "  Select,\n  Spinner,\n  Table,\n  Textarea,\n} from \"@/components/ui\";",
    )
p.write_text(t, encoding="utf-8")
print("counterparty page ok")
