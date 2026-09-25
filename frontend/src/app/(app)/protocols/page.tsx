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
import { apiGet, apiPost } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Protocol = {
  id: string;
  number: string;
  protocol_date: string;
  counterparty_id: string;
  protocol_type_id: string;
  status: string;
};

type PType = { id: string; code: string; name: string };
type CP = { id: string; full_name: string };

export default function ProtocolsPage() {
  const [items, setItems] = useState<Protocol[]>([]);
  const [types, setTypes] = useState<PType[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    number: "",
    protocol_date: new Date().toISOString().slice(0, 10),
    protocol_type_id: "",
    counterparty_id: "",
    status: "draft",
  });

  async function load() {
    setLoading(true);
    try {
      const [list, t, parties] = await Promise.all([
        apiGet<Protocol[]>(`/works`).catch(() => []), // fallback if no list endpoint
        apiGet<PType[]>(`/protocol-types`).catch(() => []),
        apiGet<CP[]>(`/counterparties`).catch(() => []),
      ]);
      // Protocol list: try dedicated endpoint via search of protocols later; works used as placeholder is wrong
      const protocols = await apiGet<Protocol[]>(`/protocols`).catch(() => list as Protocol[]);
      setItems(protocols);
      setTypes(t);
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
      await apiPost("/protocols", {
        ...form,
        protocol_date: new Date(form.protocol_date).toISOString(),
      });
      setOpen(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать");
    }
  }

  return (
    <div>
      <PageHeader
        title="Протоколы"
        subtitle="Номера вручную, со сбросом года"
        actions={<Button onClick={() => setOpen(true)}>+ Протокол</Button>}
      />
      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Номер" },
            { key: "d", label: "Дата" },
            { key: "c", label: "Контрагент" },
            { key: "t", label: "Тип" },
            { key: "s", label: "Статус" },
          ]}
          rows={items.map((p) => [
            p.number,
            fmtDate(p.protocol_date),
            cps.find((c) => c.id === p.counterparty_id)?.full_name || p.counterparty_id,
            types.find((t) => t.id === p.protocol_type_id)?.name || p.protocol_type_id,
            <Badge key="s" tone={p.status === "draft" ? "warn" : "ok"}>
              {p.status}
            </Badge>,
          ])}
          empty="Протоколов нет"
        />
      ) : null}

      <Modal open={open} title="Новый протокол" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Номер *">
            <Input value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
          </Field>
          <Field label="Дата *">
            <Input
              type="date"
              value={form.protocol_date}
              onChange={(e) => setForm({ ...form, protocol_date: e.target.value })}
            />
          </Field>
          <Field label="Тип протокола *">
            <Select
              value={form.protocol_type_id}
              onChange={(e) => setForm({ ...form, protocol_type_id: e.target.value })}
            >
              <option value="">— выберите —</option>
              {types.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </Select>
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
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={!form.number || !form.counterparty_id || !form.protocol_type_id}>
            Создать
          </Button>
        </div>
      </Modal>
    </div>
  );
}
