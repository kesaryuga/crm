from pathlib import Path

# Put CommentsInline at the top of contract detail (replace notes "Комментарий" card content)
root = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm")

# contracts
p = root / "frontend/src/app/(app)/contracts/[id]/page.tsx"
t = p.read_text(encoding="utf-8")
t = t.replace(
    'import Comments from "@/components/Comments";',
    'import Comments, { CommentsInline } from "@/components/Comments";',
)
t = t.replace(
    """        <Card title="Комментарий">
          <p className="text-sm whitespace-pre-wrap">{contract.notes || "—"}</p>
        </Card>""",
    """        <Card title="Комментарии">
          <CommentsInline entityType="contract" entityId={contract.id} limit={5} />
          {contract.notes ? (
            <p className="mt-2 text-sm text-muted">Заметки договора: {contract.notes}</p>
          ) : null}
        </Card>""",
)
p.write_text(t, encoding="utf-8")
print("contract ok", "CommentsInline" in t)

# tasks detail - already has Comments component, make inline visible at top
p = root / "frontend/src/app/(app)/tasks/[id]/page.tsx"
t = p.read_text(encoding="utf-8")
t = t.replace(
    'import Comments from "@/components/Comments";',
    'import Comments, { CommentsInline } from "@/components/Comments";',
)
if "CommentsInline" not in t.split("import")[-1]:
    # insert visible comments after header badges
    t = t.replace(
        """      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Описание">""",
        """      <div className="mb-4">
        <CommentsInline entityType="task" entityId={task.id} limit={5} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Описание">""",
    )
p.write_text(t, encoding="utf-8")
print("task ok")

# counterparties
p = root / "frontend/src/app/(app)/counterparties/[id]/page.tsx"
t = p.read_text(encoding="utf-8")
t = t.replace(
    'import Comments from "@/components/Comments";',
    'import Comments, { CommentsInline } from "@/components/Comments";',
)
if "CommentsInline" not in t.split("from")[-1]:
    t = t.replace(
        """      {tab === "Обзор" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Реквизиты">""",
        """      <div className="mb-4">
        <CommentsInline entityType="counterparty" entityId={cp.id} limit={3} />
      </div>

      {tab === "Обзор" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Реквизиты">""",
    )
p.write_text(t, encoding="utf-8")
print("cp ok")
