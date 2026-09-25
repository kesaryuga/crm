from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\components\AppShell.tsx")
t = p.read_text(encoding="utf-8")
if "/planner" not in t:
    t = t.replace(
        '{ href: "/tasks", label: "Задачи" },',
        '{ href: "/tasks", label: "Задачи" },\n      { href: "/planner", label: "Планёрка" },',
    )
if "/users" not in t:
    t = t.replace(
        '  {\n    section: "Справочники",',
        '  {\n    section: "Управление",\n    items: [{ href: "/users", label: "Пользователи" }],\n  },\n  {\n    section: "Справочники",',
    )
p.write_text(t, encoding="utf-8")
print("planner", "/planner" in t, "users", "/users" in t)
