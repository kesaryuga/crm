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
import { apiGet, apiPost } from "@/lib/api";
import { WORK_STATUSES, fmtDate } from "@/lib/format";

type Work = {
  id: string;
  number: string;
  work_date: string;
  counterparty_id: string;
  object_id: string | null;
  status: string;
  notes: string;
};

type CP = { id: string; full_name: string };

const emptyForm = {
  number: "",
  work_date: new Date().toISOString().slice(0, 10),
  counterparty_id: "",
  object_id: "",
  status: "planned",
  notes: "",
};

export default function WorksPage() {
  const [items, setItems] = useState<Work[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const names = Object.fromEntries(cps.map((c) => [c.id, c.full_name]));

  async function load() {
    setLoading(true);
    try {
      const [list, parties] = await Promise.all([apiGet<Work[]>(`/works`), apiGet<CP[]>(`/counterparties`).catch(() => [])]);
      setItems(list);
      setCps(parties);
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
      await apiPost("/works", {
        ...form,
        work_date: new Date(form.work_date).toISOString(),
        object_id: form.object_id || null,
      });
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  return (
    <div>
      <PageHeader
        title="Испытания / работы"
        subtitle="Нумерация вручную, со сбросом года"
        actions={<Button onClick={() => setOpen(true)}>+ Испытание</Button>}
      />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Номер" },
            { key: "d", label: "Дата" },
            { key: "c", label: "Контрагент" },
            { key: "s", label: "Статус" },
            { key: "no", label: "Заметки" },
          ]}
          rows={items.map((w) => [
            w.number,
            fmtDate(w.work_date),
            names[w.counterparty_id] || w.counterparty_id,
            <Badge key="s" tone={w.status === "done" ? "ok" : "info"}>
              {WORK_STATUSES[w.status] || w.status}
            </Badge>,
            w.notes || "—",
          ])}
          empty="Испытаний нет"
        />
      ) : null}

      <Modal open={open} title="Новое испытание" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Номер *">
            <Input value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
          </Field>
          <Field label="Дата *">
            <Input type="date" value={form.work_date} onChange={(e) => setForm({ ...form, work_date: e.target.value })} />
          </Field>
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
          <Field label="Статус">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {Object.entries(WORK_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <Field label="Заметки">
          <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={!form.number || !form.counterparty_id}>
            Создать
          </Button>
        </div>
      </Modal>
    </div>
  );
}
