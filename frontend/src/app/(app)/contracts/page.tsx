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
import { apiGet, apiPost } from "@/lib/api";
import { CONTRACT_STATUSES, fmtDate, fmtMoney } from "@/lib/format";

type Contract = {
  id: string;
  number: string;
  series: string;
  contract_date: string;
  counterparty_id: string;
  status: string;
  currency: string;
  total_amount: string;
  notes: string;
};

type CP = { id: string; full_name: string };

const emptyForm = {
  number: "",
  series: "",
  contract_date: new Date().toISOString().slice(0, 10),
  counterparty_id: "",
  status: "draft",
  currency: "BYN",
  notes: "",
};

export default function ContractsPage() {
  const [items, setItems] = useState<Contract[]>([]);
  const [cps, setCps] = useState<CP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");
  const names = Object.fromEntries(cps.map((c) => [c.id, c.full_name]));

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = status ? `?status=${status}` : "";
      const [list, parties] = await Promise.all([
        apiGet<Contract[]>(`/contracts${params}`),
        apiGet<CP[]>(`/counterparties`).catch(() => []),
      ]);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  async function create() {
    setSaving(true);
    try {
      await apiPost("/contracts", {
        ...form,
        contract_date: new Date(form.contract_date).toISOString(),
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

  return (
    <div>
      <PageHeader
        title="Договоры"
        subtitle="Номера вручную, со сбросом года"
        actions={<Button onClick={() => setOpen(true)}>+ Договор</Button>}
      />

      <div className="mb-4">
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-48">
          <option value="">Все статусы</option>
          {Object.entries(CONTRACT_STATUSES).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading ? (
        <Table
          columns={[
            { key: "n", label: "Номер" },
            { key: "d", label: "Дата" },
            { key: "c", label: "Контрагент" },
            { key: "s", label: "Статус" },
            { key: "a", label: "Сумма" },
          ]}
          rows={items.map((c) => [
            <Link key={c.id} href={`/contracts/${c.id}`} className="font-medium text-accent">
              {[c.series, c.number].filter(Boolean).join(" ")}
            </Link>,
            fmtDate(c.contract_date),
            names[c.counterparty_id] || c.counterparty_id,
            <Badge key="s" tone={c.status === "active" ? "ok" : "default"}>
              {CONTRACT_STATUSES[c.status] || c.status}
            </Badge>,
            fmtMoney(c.total_amount, c.currency),
          ])}
          empty="Договоров нет"
        />
      ) : null}

      <Modal open={open} title="Новый договор" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Номер *">
            <Input value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
          </Field>
          <Field label="Серия">
            <Input value={form.series} onChange={(e) => setForm({ ...form, series: e.target.value })} />
          </Field>
          <Field label="Дата *">
            <Input
              type="date"
              value={form.contract_date}
              onChange={(e) => setForm({ ...form, contract_date: e.target.value })}
            />
          </Field>
          <Field label="Контрагент *">
            <Select
              value={form.counterparty_id}
              onChange={(e) => setForm({ ...form, counterparty_id: e.target.value })}
            >
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
              {Object.entries(CONTRACT_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Валюта">
            <Input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
          </Field>
        </div>
        <Field label="Комментарий">
          <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={saving || !form.number || !form.counterparty_id}>
            {saving ? "Сохраняем…" : "Создать"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
