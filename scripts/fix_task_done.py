from pathlib import Path

# format.ts - unify statuses
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\lib\format.ts")
t = p.read_text(encoding="utf-8")
t = t.replace(
    """export const TASK_STATUSES: Record<string, string> = {
  new: "Новая",
  in_progress: "В работе",
  done: "Выполнена",
  cancelled: "Отменена",
};""",
    """export const TASK_STATUSES: Record<string, string> = {
  new: "Новая",
  in_progress: "В работе",
  completed: "Выполнена",
  done: "Выполнена",
  cancelled: "Отменена",
};""",
)
p.write_text(t, encoding="utf-8")
print("format ok")

# tasks page - simplify: no status select in list, only badge + Готово
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\app\(app)\tasks\page.tsx")
t = p.read_text(encoding="utf-8")

# replace status Select column with Badge
old_select = '''            <Select
              key="s"
              value={t.status}
              onChange={(e) => setTaskStatus(t.id, e.target.value)}
              className="h-8 w-32"
            >
              {Object.entries(TASK_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>,'''
new_badge = '''            <Badge key="s" tone={t.status === "completed" || t.status === "done" ? "ok" : t.is_overdue ? "danger" : "default"}>
              {TASK_STATUSES[t.status] || t.status}
            </Badge>,'''
if old_select in t:
    t = t.replace(old_select, new_badge)
    print("status select -> badge")

# complete button logic
t = t.replace(
    '''            <div key="a" className="flex gap-1">
              <Button variant="secondary" onClick={() => setDelegateOpen(t)}>
                Делегировать
              </Button>
              {t.status !== "done" ? (
                <Button onClick={() => complete(t.id)}>Готово</Button>
              ) : (
                <Badge tone="ok">✓</Badge>
              )}
            </div>,''',
    '''            <div key="a" className="flex gap-1">
              <Button variant="secondary" onClick={() => setDelegateOpen(t)}>
                Делегировать
              </Button>
              {t.status !== "completed" && t.status !== "done" && t.status !== "cancelled" ? (
                <Button onClick={() => complete(t.id)}>Готово</Button>
              ) : (
                <Badge tone="ok">✓</Badge>
              )}
            </div>,''',
)

# complete() should reload even if we only send empty body
t = t.replace(
    '''  async function complete(id: string) {
    await apiPost(`/tasks/${id}/complete`, { status: "done" });
    await load();
  }''',
    '''  async function complete(id: string) {
    await apiPost(`/tasks/${id}/complete`, {});
    await load();
  }''',
)

# remove setTaskStatus if unused - keep for simplicity but not in list
p.write_text(t, encoding="utf-8")
print("tasks page ok")

# upcoming filter done -> completed
p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\api\tasks.py")
t = p.read_text(encoding="utf-8")
t = t.replace('Task.status.notin_(("done", "cancelled"))', 'Task.status.notin_(("completed", "done", "cancelled"))')
p.write_text(t, encoding="utf-8")
print("tasks.py filter ok")
