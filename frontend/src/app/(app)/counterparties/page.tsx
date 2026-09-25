"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Empty,
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
import { CP_STATUSES } from "@/lib/format";

type Counterparty = {
  id: string;
  full_name: string;
  short_name: string;
  unp: string;
  phone: string;
  email: string;
  status: string;
  legal_address: string;
};

const emptyForm = {
  full_name: "",
  short_name: "",
  unp: "",
  legal_address: "",
  postal_address: "",
  phone: "",
  email: "",
  website: "",
  director_name: "",
  director_position: "",
  authority_basis: "",
  bank_name: "",
  bank_bic: "",
  bank_account: "",
  status: "active",
  notes: "",
};

export default function CounterpartiesPage() {
  const [items, setItems] = useState<Counterparty[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (status) params.set("status", status);
      const data = await apiGet<Counterparty[]>(`/counterparties${params.toString() ? `?${params}` : ""}`);
      setItems(data);
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
    setFormError(null);
    try {
      await apiPost("/counterparties", form);
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  const rows = useMemo(
    () =>
      items.map((c) => [
        <Link key={c.id} href={`/counterparties/${c.id}`} className="font-medium text-accent">
          {c.full_name}
        </Link>,
        c.unp || "—",
        c.phone || "—",
        c.email || "—",
        <Badge key="s" tone={c.status === "active" ? "ok" : "default"}>
          {CP_STATUSES[c.status] || c.status}
        </Badge>,
      ]),
    [items],
  );

  return (
    <div>
      <PageHeader
        title="Контрагенты"
        subtitle="Компании и организации"
        actions={<Button onClick={() => setOpen(true)}>+ Контрагент</Button>}
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <Input
          placeholder="Поиск по названию, УНП…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          className="w-64"
        />
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-40">
          <option value="">Все статусы</option>
          {Object.entries(CP_STATUSES).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Button variant="secondary" onClick={load}>
          Найти
        </Button>
      </div>

      {error ? <ErrorBox error={error} onRetry={load} /> : null}
      {loading ? <Spinner /> : null}
      {!loading && !error ? (
        <Table
          columns={[
            { key: "name", label: "Наименование" },
            { key: "unp", label: "УНП" },
            { key: "phone", label: "Телефон" },
            { key: "email", label: "Email" },
            { key: "status", label: "Статус" },
          ]}
          rows={rows}
          empty="Контрагентов нет. Нажмите «+ Контрагент»."
        />
      ) : null}

      <Modal open={open} title="Новый контрагент" onClose={() => setOpen(false)} wide>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Полное наименование *">
            <Input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </Field>
          <Field label="Краткое наименование">
            <Input value={form.short_name} onChange={(e) => setForm({ ...form, short_name: e.target.value })} />
          </Field>
          <Field label="УНП">
            <Input value={form.unp} onChange={(e) => setForm({ ...form, unp: e.target.value })} />
          </Field>
          <Field label="Статус">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {Object.entries(CP_STATUSES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Юридический адрес">
            <Input value={form.legal_address} onChange={(e) => setForm({ ...form, legal_address: e.target.value })} />
          </Field>
          <Field label="Почтовый адрес">
            <Input value={form.postal_address} onChange={(e) => setForm({ ...form, postal_address: e.target.value })} />
          </Field>
          <Field label="Телефон">
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label="Email">
            <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <Field label="Руководитель">
            <Input value={form.director_name} onChange={(e) => setForm({ ...form, director_name: e.target.value })} />
          </Field>
          <Field label="Должность руководителя">
            <Input
              value={form.director_position}
              onChange={(e) => setForm({ ...form, director_position: e.target.value })}
            />
          </Field>
          <Field label="Банк">
            <Input value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} />
          </Field>
          <Field label="Р/с">
            <Input value={form.bank_account} onChange={(e) => setForm({ ...form, bank_account: e.target.value })} />
          </Field>
        </div>
        {formError ? <p className="mt-3 text-sm text-red-600">{formError}</p> : null}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={create} disabled={saving || !form.full_name.trim()}>
            {saving ? "Сохраняем…" : "Сохранить"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
