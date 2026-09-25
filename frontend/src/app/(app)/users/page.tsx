"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  ErrorBox,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
  Spinner,
  Table,
} from "@/components/ui";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";

type Role = { id: string; code: string; name: string; permissions: string[] };
type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  role_id: string | null;
  role_code: string | null;
  role_name: string | null;
  permissions: string[];
  last_login_at: string | null;
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role_id: "",
    is_active: true,
  });
  const [password, setPassword] = useState("");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [u, r] = await Promise.all([apiGet<User[]>(`/users`), apiGet<Role[]>(`/roles`)]);
      setUsers(u);
      setRoles(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function create() {
    try {
      await apiPost("/users", { ...form, password: form.password || "temp2026" });
      setOpen(false);
      setForm({ email: "", password: "", first_name: "", last_name: "", role_id: "", is_active: true });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  async function saveEdit() {
    if (!editUser) return;
    try {
      await apiPatch(`/users/${editUser.id}`, {
        first_name: editUser.first_name,
        last_name: editUser.last_name,
        role_id: editUser.role_id,
        is_active: editUser.is_active,
        ...(password ? { password } : {}),
      });
      setEditUser(null);
      setPassword("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    }
  }

  return (
    <div>
      <PageHeader
        title="Пользователи"
        subtitle="Учётки, роли и права"
        actions={<Button onClick={() => setOpen(true)}>+ Пользователь</Button>}
      />

      <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
        <b>Тестовые учётки:</b> boss@kit-lab.by / boss2026 (руководитель) · manager@kit-lab.by / manager2026 ·
        engineer@kit-lab.by / engineer2026
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Сотрудник" },
            { key: "e", label: "Email" },
            { key: "r", label: "Роль" },
            { key: "s", label: "Активен" },
            { key: "l", label: "Вход" },
            { key: "a", label: "" },
          ]}
          rows={users.map((u) => [
            <div key={u.id}>
              <div className="font-medium">
                {u.last_name} {u.first_name}
              </div>
              <div className="text-xs text-muted">{u.permissions.slice(0, 4).join(", ")}</div>
            </div>,
            u.email,
            <Badge key="r" tone={u.role_code === "boss" || u.role_code === "admin" ? "info" : "default"}>
              {u.role_name || u.role_code || "—"}
            </Badge>,
            u.is_active ? "✓" : "—",
            fmtDateTime(u.last_login_at),
            <Button key="a" variant="secondary" onClick={() => setEditUser(u)}>
              Права
            </Button>,
          ])}
          empty="Пользователей нет"
        />
      ) : null}

      <Modal open={open} title="Новый пользователь" onClose={() => setOpen(false)}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Email *">
            <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <Field label="Пароль *">
            <Input value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Field>
          <Field label="Имя">
            <Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </Field>
          <Field label="Фамилия">
            <Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </Field>
          <Field label="Роль">
            <Select value={form.role_id} onChange={(e) => setForm({ ...form, role_id: e.target.value })}>
              <option value="">— без роли —</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={!form.email || !form.password}>
            Создать
          </Button>
        </div>
      </Modal>

      <Modal open={!!editUser} title="Права и роль" onClose={() => setEditUser(null)}>
        {editUser ? (
          <div className="grid gap-3">
            <Field label="Фамилия">
              <Input
                value={editUser.last_name}
                onChange={(e) => setEditUser({ ...editUser, last_name: e.target.value })}
              />
            </Field>
            <Field label="Имя">
              <Input
                value={editUser.first_name}
                onChange={(e) => setEditUser({ ...editUser, first_name: e.target.value })}
              />
            </Field>
            <Field label="Роль">
              <Select
                value={editUser.role_id || ""}
                onChange={(e) => setEditUser({ ...editUser, role_id: e.target.value })}
              >
                <option value="">— без роли —</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.code})
                  </option>
                ))}
              </Select>
            </Field>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={editUser.is_active}
                onChange={(e) => setEditUser({ ...editUser, is_active: e.target.checked })}
              />
              Активен (доступ разрешён)
            </label>
            <Field label="Новый пароль (пусто — не менять)">
              <Input value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <div className="rounded-md bg-slate-50 p-3 text-xs text-muted">
              Права роли:{" "}
              {(roles.find((r) => r.id === editUser.role_id)?.permissions || editUser.permissions).join(", ") || "—"}
            </div>
          </div>
        ) : null}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setEditUser(null)}>
            Отмена
          </Button>
          <Button onClick={saveEdit}>Сохранить</Button>
        </div>
      </Modal>
    </div>
  );
}
