"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  ErrorBox,
  Field,
  Input,
  Modal,
  PageHeader,
  Spinner,
  Table,
} from "@/components/ui";
import { apiGet, apiPatch, apiPost } from "@/lib/api";

type Role = { id: string; code: string; name: string; permissions: string[] };

const GROUPS: { title: string; codes: string[] }[] = [
  { title: "CRM", codes: ["crm.view", "crm.edit"] },
  { title: "Задачи", codes: ["tasks.view", "tasks.create", "tasks.edit", "tasks.delegate"] },
  { title: "Договоры", codes: ["contracts.view", "contracts.create", "contracts.edit"] },
  { title: "Испытания", codes: ["works.view", "works.edit"] },
  { title: "Протоколы", codes: ["protocols.view", "protocols.edit"] },
  { title: "Оборудование", codes: ["equipment.view", "equipment.edit"] },
  { title: "Документы и данные", codes: ["documents.generate", "export", "services.view"] },
  { title: "Администрирование", codes: ["users.view", "users.manage", "audit.view", "admin.all"] },
];

const LABELS: Record<string, string> = {
  "admin.all": "Полный доступ (включает всё)",
  "crm.view": "Просмотр контрагентов",
  "crm.edit": "Создание и правка контрагентов",
  "tasks.view": "Просмотр задач",
  "tasks.create": "Создание задач",
  "tasks.edit": "Правка задач",
  "tasks.delegate": "Делегирование задач",
  "contracts.view": "Просмотр договоров",
  "contracts.create": "Создание договоров",
  "contracts.edit": "Правка договоров",
  "works.view": "Просмотр испытаний",
  "works.edit": "Правка испытаний",
  "protocols.view": "Просмотр протоколов",
  "protocols.edit": "Правка протоколов",
  "equipment.view": "Просмотр оборудования",
  "equipment.edit": "Правка оборудования",
  "services.view": "Просмотр услуг",
  "documents.generate": "Генерация документов",
  export: "Экспорт CSV/XLSX",
  "users.view": "Просмотр пользователей",
  "users.manage": "Управление пользователями",
  "audit.view": "Журнал действий",
};

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState<Role | null>(null);
  const [form, setForm] = useState({ code: "", name: "" });
  const [perms, setPerms] = useState<string[]>([]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setRoles(await apiGet<Role[]>(`/roles`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openCreate() {
    setEdit(null);
    setForm({ code: "", name: "" });
    setPerms(["crm.view", "tasks.view", "tasks.create"]);
    setOpen(true);
  }

  function openEdit(role: Role) {
    setEdit(role);
    setForm({ code: role.code, name: role.name });
    setPerms(role.permissions);
    setOpen(true);
  }

  function toggle(code: string) {
    if (code === "admin.all") {
      setPerms((p) => (p.includes("admin.all") ? [] : ["admin.all"]));
      return;
    }
    setPerms((p) => {
      const withoutAdmin = p.filter((x) => x !== "admin.all");
      return withoutAdmin.includes(code)
        ? withoutAdmin.filter((x) => x !== code)
        : [...withoutAdmin, code];
    });
  }

  async function save() {
    try {
      if (edit) {
        await apiPatch(`/roles/${edit.id}`, { name: form.name, permissions: perms });
      } else {
        await apiPost("/roles", { code: form.code, name: form.name, permissions: perms });
      }
      setOpen(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить роль");
    }
  }

  const summary = useMemo(() => {
    if (perms.includes("admin.all")) return "Полный доступ ко всему";
    return perms.map((c) => LABELS[c] || c).join(" · ") || "Прав нет";
  }, [perms]);

  return (
    <div>
      <PageHeader
        title="Роли и права"
        subtitle="Конструктор ролей: отметьте права и сохраните"
        actions={<Button onClick={openCreate}>+ Роль</Button>}
      />

      <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
        Роли — <b>внутри CRM</b> (не Supabase). Назначение роли пользователю: раздел{" "}
        <b>Пользователи → кнопка «Права»</b>.
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Роль" },
            { key: "c", label: "Код" },
            { key: "p", label: "Права" },
            { key: "a", label: "" },
          ]}
          rows={roles.map((r) => [
            <div key={r.id} className="font-medium">
              {r.name}
            </div>,
            <code key="c" className="text-xs text-muted">
              {r.code}
            </code>,
            <div key="p" className="text-xs text-muted">
              {r.permissions.includes("admin.all") ? (
                <Badge tone="info">полный доступ</Badge>
              ) : (
                r.permissions.slice(0, 6).join(", ")
              )}
              {r.permissions.length > 6 && !r.permissions.includes("admin.all")
                ? ` +${r.permissions.length - 6}`
                : ""}
            </div>,
            <Button key="a" variant="secondary" onClick={() => openEdit(r)}>
              Редактировать
            </Button>,
          ])}
          empty="Ролей нет"
        />
      ) : null}

      <Modal open={open} title={edit ? `Роль: ${edit.name}` : "Новая роль"} onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          {!edit ? (
            <Field label="Код роли * (латиницей)">
              <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="supervisor" />
            </Field>
          ) : (
            <Field label="Код роли">
              <Input value={form.code} disabled />
            </Field>
          )}
          <Field label="Название *">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Старший менеджер" />
          </Field>
        </div>

        <div className="mt-4 rounded-lg border border-line p-3">
          <div className="mb-2 text-sm font-semibold">Права</div>
          <label className="mb-3 flex items-center gap-2 rounded-md bg-slate-50 p-2 text-sm">
            <input
              type="checkbox"
              checked={perms.includes("admin.all")}
              onChange={() => toggle("admin.all")}
            />
            <span className="font-medium">Полный доступ (admin.all)</span>
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            {GROUPS.map((g) => (
              <div key={g.title} className="rounded-md border border-line p-2">
                <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{g.title}</div>
                <div className="space-y-1">
                  {g.codes
                    .filter((c) => c !== "admin.all")
                    .map((c) => (
                      <label key={c} className="flex items-start gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="mt-1"
                          disabled={perms.includes("admin.all")}
                          checked={perms.includes(c)}
                          onChange={() => toggle(c)}
                        />
                        <span>{LABELS[c] || c}</span>
                      </label>
                    ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="mt-3 text-xs text-muted">Итого: {summary}</p>

        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={save} disabled={!form.name.trim() || (!edit && !form.code.trim())}>
            Сохранить роль
          </Button>
        </div>
      </Modal>
    </div>
  );
}
