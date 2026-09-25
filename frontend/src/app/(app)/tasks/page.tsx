"use client";

import Link from "next/link";
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
  Textarea,
} from "@/components/ui";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { PRIORITIES, TASK_STATUSES, TASK_TYPES, fmtDateTime } from "@/lib/format";

type Task = {
  id: string;
  title: string;
  description: string;
  task_type: string;
  status: string;
  priority: string;
  due_at: string | null;
  is_overdue: boolean;
  counterparty_id: string | null;
  assignee_user_id: string | null;
  creator_user_id: string | null;
};

type User = { id: string; first_name: string; last_name: string; email: string; role_name: string | null };

const emptyForm = {
  title: "",
  description: "",
  task_type: "other",
  priority: "medium",
  status: "new",
  due_at: "",
  counterparty_id: "",
  assignee_user_id: "",
};

export default function TasksPage() {
  const [items, setItems] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [counterparties, setCounterparties] = useState<{ id: string; full_name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");
  const [overdue, setOverdue] = useState(false);
  const [assignee, setAssignee] = useState("");
  const [delegateOpen, setDelegateOpen] = useState<Task | null>(null);
  const [delegateId, setDelegateId] = useState("");
  const [delegateComment, setDelegateComment] = useState("");

  const userName = (id: string | null) => {
    if (!id) return "—";
    const u = users.find((x) => x.id === id);
    return u ? `${u.last_name} ${u.first_name}` : id.slice(0, 8);
  };

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (overdue) params.set("overdue", "true");
      if (assignee) params.set("assignee_user_id", assignee);
      const [list, u, cps] = await Promise.all([
        apiGet<Task[]>(`/tasks${params.toString() ? `?${params}` : ""}`),
        apiGet<User[]>(`/users`).catch(() => []),
        apiGet<{ id: string; full_name: string }[]>(`/counterparties`).catch(() => []),
      ]);
      setItems(list);
      setUsers(u);
      setCounterparties(cps);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, overdue, assignee]);

  async function create() {
    setSaving(true);
    try {
      await apiPost("/tasks", {
        ...form,
        due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
        counterparty_id: form.counterparty_id || null,
        assignee_user_id: form.assignee_user_id || null,
      });
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    } finally {
      setSaving(false);
    }
  }

  async function complete(id: string) {
    await apiPost(`/tasks/${id}/complete`, { status: "done" });
    await load();
  }

  async function setTaskStatus(id: string, next: string) {
    await apiPatch(`/tasks/${id}`, { status: next });
    await load();
  }

  async function delegate() {
    if (!delegateOpen) return;
    await apiPost(`/tasks/${delegateOpen.id}/delegate`, {
      assignee_user_id: delegateId,
      comment: delegateComment,
    });
    setDelegateOpen(null);
    setDelegateComment("");
    await load();
  }

  return (
    <div>
      <PageHeader title="Задачи" subtitle="Звонки, встречи, документы, испытания" actions={<Button onClick={() => setOpen(true)}>+ Задача</Button>} />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-44">
          <option value="">Все статусы</option>
          {Object.entries(TASK_STATUSES).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Select value={assignee} onChange={(e) => setAssignee(e.target.value)} className="w-52">
          <option value="">Все исполнители</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.last_name} {u.first_name}
            </option>
          ))}
        </Select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={overdue} onChange={(e) => setOverdue(e.target.checked)} />
          Только просроченные
        </label>
        <Link href="/planner" className="ml-auto text-sm text-accent">
          Планёрка →
        </Link>
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "t", label: "Задача" },
            { key: "ty", label: "Тип" },
            { key: "as", label: "Исполнитель" },
            { key: "s", label: "Статус" },
            { key: "d", label: "Срок" },
            { key: "a", label: "" },
          ]}
          rows={items.map((t) => [
            <div key={t.id}>
              <Link href={`/tasks/${t.id}`} className="font-medium text-accent">
                {t.title}
              </Link>
              {t.is_overdue ? (
                <Badge tone="danger">просрочено</Badge>
              ) : null}
            </div>,
            TASK_TYPES[t.task_type] || t.task_type,
            userName(t.assignee_user_id),
            <Select
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
            </Select>,
            fmtDateTime(t.due_at),
            <div key="a" className="flex gap-1">
              <Button variant="secondary" onClick={() => setDelegateOpen(t)}>
                Делегировать
              </Button>
              {t.status !== "done" ? (
                <Button onClick={() => complete(t.id)}>Готово</Button>
              ) : (
                <Badge tone="ok">✓</Badge>
              )}
            </div>,
          ])}
          empty="Задач нет"
        />
      ) : null}

      <Modal open={open} title="Новая задача" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Заголовок *">
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </Field>
          <Field label="Тип">
            <Select value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value })}>
              {Object.entries(TASK_TYPES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Исполнитель">
            <Select
              value={form.assignee_user_id}
              onChange={(e) => setForm({ ...form, assignee_user_id: e.target.value })}
            >
              <option value="">— не назначен —</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.last_name} {u.first_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Приоритет">
            <Select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              {Object.entries(PRIORITIES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Срок">
            <Input
              type="datetime-local"
              value={form.due_at}
              onChange={(e) => setForm({ ...form, due_at: e.target.value })}
            />
          </Field>
          <Field label="Контрагент (необязательно)">
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
          </Field>
        </div>
        <Field label="Описание">
          <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={saving || !form.title.trim()}>
            {saving ? "Сохраняем…" : "Создать"}
          </Button>
        </div>
      </Modal>

      <Modal open={!!delegateOpen} title="Делегировать задачу" onClose={() => setDelegateOpen(null)}>
        <p className="mb-3 text-sm text-muted">{delegateOpen?.title}</p>
        <div className="grid gap-3">
          <Field label="Исполнитель *">
            <Select value={delegateId} onChange={(e) => setDelegateId(e.target.value)}>
              <option value="">— выберите —</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.last_name} {u.first_name} ({u.role_name || "—"})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Комментарий">
            <Textarea value={delegateComment} onChange={(e) => setDelegateComment(e.target.value)} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDelegateOpen(null)}>
            Отмена
          </Button>
          <Button onClick={delegate} disabled={!delegateId}>
            Делегировать
          </Button>
        </div>
      </Modal>
    </div>
  );
}
