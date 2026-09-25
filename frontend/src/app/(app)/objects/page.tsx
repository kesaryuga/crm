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
  Textarea,
} from "@/components/ui";
import Comments from "@/components/Comments";
import { apiGet, apiPatch, apiPost } from "@/lib/api";

type Obj = {
  id: string;
  counterparty_id: string;
  name: string;
  address: string;
  phone: string;
  description: string;
  status: string;
};

type CP = { id: string; full_name: string };

const STATUSES = [
  { value: "active", label: "Активный" },
  { value: "archived", label: "Архив" },
  { value: "inactive", label: "Неактивный" },
];

export default function ObjectsPage() {
  const [items, setItems] = useState<Obj[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [editObj, setEditObj] = useState<Obj | null>(null);
  const [commentObj, setCommentObj] = useState<Obj | null>(null);
  const [form, setForm] = useState({
    counterparty_id: "",
    name: "",
    address: "",
    phone: "",
    description: "",
    status: "active",
  });

  const names = Object.fromEntries(cps.map((c) => [c.id, c.full_name]));

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const parties = await apiGet<CP[]>(`/counterparties`).catch(() => []);
      setCps(parties);
      const all: Obj[] = [];
      for (const cp of parties.slice(0, 50)) {
        const objs = await apiGet<Obj[]>(`/counterparties/${cp.id}/objects`).catch(() => []);
        all.push(...objs);
      }
      setItems(all);
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
      await apiPost("/objects", form);
      setOpen(false);
      setForm({ counterparty_id: "", name: "", address: "", phone: "", description: "", status: "active" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  async function saveEdit() {
    if (!editObj) return;
    try {
      await apiPatch(`/objects/${editObj.id}`, {
        name: editObj.name,
        address: editObj.address,
        phone: editObj.phone,
        description: editObj.description,
        status: editObj.status,
      });
      setEditObj(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    }
  }

  return (
    <div>
      <PageHeader
        title="Объекты"
        subtitle="Места проведения работ"
        actions={<Button onClick={() => setOpen(true)}>+ Объект</Button>}
      />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Название" },
            { key: "a", label: "Адрес" },
            { key: "c", label: "Контрагент" },
            { key: "s", label: "Статус" },
            { key: "x", label: "" },
          ]}
          rows={items.map((o) => [
            <div key={o.id}>
              <div className="font-medium">{o.name}</div>
              <div className="text-xs text-muted">{o.phone || ""}</div>
            </div>,
            o.address || "—",
            names[o.counterparty_id] || o.counterparty_id,
            <Badge key="s" tone={o.status === "active" ? "ok" : "default"}>
              {STATUSES.find((s) => s.value === o.status)?.label || o.status}
            </Badge>,
            <div key="x" className="flex gap-1">
              <Button variant="secondary" onClick={() => setEditObj(o)}>
                Изменить
              </Button>
              <Button variant="ghost" onClick={() => setCommentObj(o)}>
                💬
              </Button>
            </div>,
          ])}
          empty="Объектов нет"
        />
      ) : null}

      <Modal open={open} title="Новый объект" onClose={() => setOpen(false)}>
        <div className="grid gap-3">
          <Field label="Контрагент *">
            <Select value={form.counterparty_id} onChange={(e) => setForm({ ...form, counterparty_id: e.target.value })}>
              <option value="">— выберите —</option>
              {cps.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Название *">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Адрес">
            <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>
          <Field label="Телефон">
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label="Описание">
            <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={!form.name || !form.counterparty_id}>
            Сохранить
          </Button>
        </div>
      </Modal>

      <Modal open={!!editObj} title="Изменить объект" onClose={() => setEditObj(null)} wide>
        {editObj ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Название *">
              <Input value={editObj.name} onChange={(e) => setEditObj({ ...editObj, name: e.target.value })} />
            </Field>
            <Field label="Статус">
              <Select value={editObj.status} onChange={(e) => setEditObj({ ...editObj, status: e.target.value })}>
                {STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Адрес">
              <Input value={editObj.address} onChange={(e) => setEditObj({ ...editObj, address: e.target.value })} />
            </Field>
            <Field label="Телефон">
              <Input value={editObj.phone} onChange={(e) => setEditObj({ ...editObj, phone: e.target.value })} />
            </Field>
            <div className="sm:col-span-2">
              <Field label="Описание">
                <Textarea
                  value={editObj.description}
                  onChange={(e) => setEditObj({ ...editObj, description: e.target.value })}
                />
              </Field>
            </div>
          </div>
        ) : null}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setEditObj(null)}>
            Отмена
          </Button>
          <Button onClick={saveEdit}>Сохранить</Button>
        </div>
      </Modal>

      <Modal
        open={!!commentObj}
        title={`Комментарии — ${commentObj?.name || ""}`}
        onClose={() => setCommentObj(null)}
        wide
      >
        {commentObj ? <Comments entityType="object" entityId={commentObj.id} title="Комментарии к объекту" /> : null}
      </Modal>
    </div>
  );
}
