"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge, Button, ErrorBox, Field, Input, Modal, PageHeader, Select, Spinner, Table, Textarea } from "@/components/ui";
import { apiGet, apiPost } from "@/lib/api";

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

export default function ObjectsPage() {
  const [items, setItems] = useState<Obj[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
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
    try {
      // objects list via counterparties' objects; also try global search later
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
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  return (
    <div>
      <PageHeader title="Объекты" subtitle="Места проведения работ" actions={<Button onClick={() => setOpen(true)}>+ Объект</Button>} />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Название" },
            { key: "a", label: "Адрес" },
            { key: "c", label: "Контрагент" },
            { key: "s", label: "Статус" },
          ]}
          rows={items.map((o) => [
            o.name,
            o.address || "—",
            names[o.counterparty_id] || o.counterparty_id,
            <Badge key="s" tone={o.status === "active" ? "ok" : "default"}>
              {o.status}
            </Badge>,
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
    </div>
  );
}
