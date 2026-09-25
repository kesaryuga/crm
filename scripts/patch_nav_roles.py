from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\components\AppShell.tsx")
t = p.read_text(encoding="utf-8")
old = 'items: [{ href: "/users", label: "Пользователи" }],'
new = (
    "items: [\n"
    '      { href: "/users", label: "Пользователи" },\n'
    '      { href: "/roles", label: "Роли и права" },\n'
    "    ],"
)
if "/roles" not in t:
    if old not in t:
        raise SystemExit("nav pattern missing")
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
print("ok", "/roles" in t)
